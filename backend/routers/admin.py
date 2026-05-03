from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from jose import jwt, JWTError
import io
from openpyxl import Workbook

from database import get_db
from config import settings
from models.student import Student
from models.check_record import CheckRecord
from models.user import User
from schemas.admin import (
    DashboardResponse, BuildingProgress, AnomalySummary,
    AnomaliesResponse, AnomalyItem, ReportResponse, GenerateReportRequest, ImportResponse,
)
from schemas.auth import ApiResponse
from services.importer import import_students_from_excel

router = APIRouter(prefix="/api/admin", tags=["管理员端"])

ALL_BUILDINGS = [7, 10, 11, 17, 19]


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


@router.get("/dashboard", response_model=ApiResponse)
def get_dashboard(
    date: date,
    db=Depends(get_db),
    _=Depends(get_admin_user),
):
    # 每栋楼的完成情况
    buildings = []
    for b in ALL_BUILDINGS:
        # 总寝室数
        total = (
            db.query(func.count(func.distinct(Student.room)))
            .filter(Student.building == b, Student.room.isnot(None))
            .scalar()
        )
        # 已查寝室数
        checked = (
            db.query(func.count(func.distinct(CheckRecord.room)))
            .filter(CheckRecord.check_date == date, CheckRecord.building == b)
            .scalar()
        )
        # 完成时间（取该楼栋最后一条提交时间）
        finished_at = (
            db.query(func.max(CheckRecord.submitted_at))
            .filter(CheckRecord.check_date == date, CheckRecord.building == b)
            .scalar()
        )
        buildings.append(
            BuildingProgress(
                building=b,
                checked_rooms=checked or 0,
                total_rooms=total or 0,
                finished_at=finished_at,
            )
        )

    # 异常汇总
    total_missing = (
        db.query(func.count(CheckRecord.id))
        .filter(CheckRecord.check_date == date, CheckRecord.anomaly_type == "应在未在")
        .scalar()
    )
    total_unreported = (
        db.query(func.count(CheckRecord.id))
        .filter(CheckRecord.check_date == date, CheckRecord.anomaly_type == "应离已返")
        .scalar()
    )

    return ApiResponse(
        data=DashboardResponse(
            buildings=buildings,
            anomaly_summary=AnomalySummary(
                total=(total_missing or 0) + (total_unreported or 0),
                missing=total_missing or 0,
                unreported_return=total_unreported or 0,
            ),
        ).model_dump()
    )


@router.get("/anomalies", response_model=ApiResponse)
def get_anomalies(
    date: date,
    building: int | None = None,
    type: str | None = None,
    counselor: str | None = None,
    db=Depends(get_db),
    _=Depends(get_admin_user),
):
    query = (
        db.query(CheckRecord, Student)
        .join(Student, CheckRecord.student_id == Student.student_id)
        .filter(CheckRecord.check_date == date, CheckRecord.anomaly_type.isnot(None))
    )

    if building:
        query = query.filter(CheckRecord.building == building)
    if type:
        query = query.filter(CheckRecord.anomaly_type == type)
    if counselor:
        query = query.filter(Student.counselor == counselor)

    items = []
    for rec, student in query.all():
        items.append(
            AnomalyItem(
                date=rec.check_date,
                building=rec.building,
                room=rec.room,
                student_id=rec.student_id,
                name=student.name,
                counselor=student.counselor,
                anomaly_type=rec.anomaly_type,
                checker=rec.checker,
                submitted_at=rec.submitted_at,
            )
        )

    return ApiResponse(data=AnomaliesResponse(items=items).model_dump())


@router.post("/import-students", response_model=ApiResponse)
async def import_students(
    file: UploadFile = File(...),
    db=Depends(get_db),
    _=Depends(get_admin_user),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        return ApiResponse(code=4002, data=None, message="仅支持 .xlsx 或 .xls 文件")

    content = await file.read()
    import io, traceback
    try:
        result = import_students_from_excel(db, io.BytesIO(content))
    except Exception as e:
        err = traceback.format_exc()
        print("Import error:", err)
        return ApiResponse(code=4003, data=None, message=f"Excel 解析失败: {e}")

    return ApiResponse(data=ImportResponse(**result).model_dump())


@router.get("/export")
def export_anomalies(
    date: date,
    building: int | None = None,
    type: str | None = None,
    counselor: str | None = None,
    db=Depends(get_db),
    _=Depends(get_admin_user),
):
    query = (
        db.query(CheckRecord, Student)
        .join(Student, CheckRecord.student_id == Student.student_id)
        .filter(CheckRecord.check_date == date, CheckRecord.anomaly_type.isnot(None))
    )

    if building:
        query = query.filter(CheckRecord.building == building)
    if type:
        query = query.filter(CheckRecord.anomaly_type == type)
    if counselor:
        query = query.filter(Student.counselor == counselor)

    wb = Workbook()
    ws = wb.active
    ws.title = "异常明细"
    ws.append(["日期", "楼栋", "寝室", "学号", "姓名", "辅导员", "异常类型", "宿管", "提交时间"])

    for rec, student in query.all():
        ws.append([
            rec.check_date.isoformat(),
            rec.building,
            rec.room,
            rec.student_id,
            student.name,
            student.counselor,
            rec.anomaly_type,
            rec.checker,
            rec.submitted_at.isoformat() if rec.submitted_at else "",
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=anomalies_{date}.xlsx"},
    )
