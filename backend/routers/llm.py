"""
简报生成路由（F-08 & F-10）

- GET /report: 获取已生成的简报
- POST /report/generate: 强制重新生成简报
- 调用失败时返回兜底原始数据
"""

from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Header
from jose import jwt, JWTError

from database import get_db
from config import settings
from models.check_record import CheckRecord
from models.student import Student
from schemas.admin import ReportResponse
from schemas.auth import ApiResponse
from services.llm_client import generate_report

router = APIRouter(prefix="/api/admin", tags=["简报生成"])


def get_admin_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="非管理员账号")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效")


def build_fallback_report(db, check_date: date) -> str:
    """生成兜底简报（原始结构化数据）"""
    anomalies = (
        db.query(CheckRecord, Student)
        .join(Student, CheckRecord.student_id == Student.student_id)
        .filter(
            CheckRecord.check_date == check_date,
            CheckRecord.anomaly_type.isnot(None),
        )
        .all()
    )

    by_counselor: dict[str, list] = {}
    for rec, student in anomalies:
        key = student.counselor
        by_counselor.setdefault(key, []).append(
            f"{rec.building}号楼 {rec.room} {student.name} ({student.student_id})"
        )

    lines = []
    missing = [r for r, _ in anomalies if r.anomaly_type == "应在未在"]
    returned = [r for r, _ in anomalies if r.anomaly_type == "应离已返"]

    if missing:
        lines.append("【应在未在（疑似失联）】")
        for rec, student in anomalies:
            if rec.anomaly_type == "应在未在":
                lines.append(f"- {student.counselor}: {rec.building}号楼 {rec.room} {student.name}")

    if returned:
        lines.append("【应离已返（已返校未报备）】")
        for rec, student in anomalies:
            if rec.anomaly_type == "应离已返":
                lines.append(f"- {student.counselor}: {rec.building}号楼 {rec.room} {student.name}")

    return "\n".join(lines) if lines else "今晚查寝无异常"


@router.get("/report", response_model=ApiResponse)
def get_report(
    date: date,
    db=Depends(get_db),
    _=Depends(get_admin_user),
):
    # 目前不做持久化存储，每次实时生成
    # 如果 LLM 调用失败，返回兜底文本
    missing_list, returned_list = _get_anomaly_lists(db, date)

    if not missing_list and not returned_list:
        return ApiResponse(data=ReportResponse(report="今晚查寝无异常").model_dump())

    try:
        report = generate_report(
            date.isoformat(),
            missing_list,
            returned_list,
        )
        return ApiResponse(
            data=ReportResponse(report=report, generated_at=datetime.utcnow()).model_dump()
        )
    except Exception as e:
        fallback = build_fallback_report(db, date)
        return ApiResponse(
            data=ReportResponse(
                report=f"[AI 简报生成失败，以下是原始数据]\n{fallback}",
                generated_at=None,
            ).model_dump()
        )


@router.post("/report/generate", response_model=ApiResponse)
def generate_new_report(
    body: GenerateReportRequest,
    db=Depends(get_db),
    _=Depends(get_admin_user),
):
    missing_list, returned_list = _get_anomaly_lists(db, body.date)

    if not missing_list and not returned_list:
        return ApiResponse(data=ReportResponse(report="今晚查寝无异常").model_dump())

    try:
        report = generate_report(
            body.date.isoformat(),
            missing_list,
            returned_list,
        )
        return ApiResponse(
            data=ReportResponse(report=report, generated_at=datetime.utcnow()).model_dump()
        )
    except Exception:
        fallback = build_fallback_report(db, body.date)
        return ApiResponse(
            data=ReportResponse(
                report=f"[AI 简报生成失败，以下是原始数据]\n{fallback}",
            ).model_dump()
        )


def _get_anomaly_lists(db, check_date: date):
    """提取异常记录并格式化为 LLM 输入列表"""
    anomalies = (
        db.query(CheckRecord, Student)
        .join(Student, CheckRecord.student_id == Student.student_id)
        .filter(
            CheckRecord.check_date == check_date,
            CheckRecord.anomaly_type == "应在未在",
        )
        .all()
    )
    missing_list = [
        f"{rec.building}号楼 {rec.room} {student.name} (辅导员: {student.counselor})"
        for rec, student in anomalies
    ]

    returned = (
        db.query(CheckRecord, Student)
        .join(Student, CheckRecord.student_id == Student.student_id)
        .filter(
            CheckRecord.check_date == check_date,
            CheckRecord.anomaly_type == "应离已返",
        )
        .all()
    )
    returned_list = [
        f"{rec.building}号楼 {rec.room} {student.name} (辅导员: {student.counselor})"
        for rec, student in returned
    ]
    return missing_list, returned_list
