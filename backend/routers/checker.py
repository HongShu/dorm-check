from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import func, and_
from jose import jwt, JWTError

from database import get_db
from config import settings
from models.student import Student
from models.check_record import CheckRecord
from models.user import User
from schemas.checker import (
    RoomsResponse, RoomCard, RoomDetailResponse,
    StudentInfo, OffCampusStudent, SubmitRequest, SubmitResponse, FinishResponse,
)
from schemas.auth import ApiResponse
from services.anomaly import determine_anomaly

router = APIRouter(prefix="/api/checker", tags=["宿管端"])


def get_checker_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "checker":
            raise HTTPException(status_code=403, detail="非宿管账号")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效")


@router.get("/rooms", response_model=ApiResponse)
def get_rooms(
    date: date,
    db=Depends(get_db),
    user: dict = Depends(get_checker_user),
):
    username = user["sub"]
    u = db.get(User, username)
    building = u.assigned_building

    # 该楼栋所有寝室
    rooms_raw = (
        db.query(Student.room, func.count(Student.student_id).label("expected_count"))
        .filter(Student.building == building, Student.room.isnot(None))
        .group_by(Student.room)
        .all()
    )

    # 已提交的查寝记录（该日期该楼栋）
    checked_raw = (
        db.query(CheckRecord.room, func.count(CheckRecord.id).label("checked_count"))
        .filter(CheckRecord.check_date == date, CheckRecord.building == building)
        .group_by(CheckRecord.room)
        .all()
    )
    checked_map = {r.room: r.checked_count for r in checked_raw}

    # 异常数
    anomaly_raw = (
        db.query(CheckRecord.room, func.count(CheckRecord.id).label("anomaly_count"))
        .filter(
            CheckRecord.check_date == date,
            CheckRecord.building == building,
            CheckRecord.anomaly_type.isnot(None),
        )
        .group_by(CheckRecord.room)
        .all()
    )
    anomaly_map = {r.room: r.anomaly_count for r in anomaly_raw}

    rooms = []
    for r in rooms_raw:
        checked = r.room in checked_map
        rooms.append(
            RoomCard(
                room=r.room,
                expected_count=r.expected_count,
                checked=checked,
                anomaly_count=anomaly_map.get(r.room, 0),
            )
        )

    # 按查寝状态（未查优先）排序，再按寝室号排序
    rooms.sort(key=lambda x: (x.checked, x.room))
    return ApiResponse(data=RoomsResponse(building=building, date=date, rooms=rooms).model_dump())


@router.get("/rooms/{room}", response_model=ApiResponse)
def get_room_detail(
    room: str,
    date: date,
    db=Depends(get_db),
    user: dict = Depends(get_checker_user),
):
    username = user["sub"]
    u = db.get(User, username)
    building = u.assigned_building

    # 应在校学生
    expected = (
        db.query(Student)
        .filter(Student.building == building, Student.room == room, Student.status == "在校")
        .all()
    )

    # 已提交的该寝室记录
    existing = (
        db.query(CheckRecord)
        .filter(
            CheckRecord.check_date == date,
            CheckRecord.building == building,
            CheckRecord.room == room,
        )
        .all()
    )
    existing_map = {r.student_id: r for r in existing}

    expected_students = []
    for s in expected:
        rec = existing_map.get(s.student_id)
        expected_students.append(
            StudentInfo(
                student_id=s.student_id,
                name=s.name,
                is_present=rec.is_present if rec else None,
            )
        )

    # 离校学生（用于"添加返校"场景）
    off_campus = (
        db.query(Student)
        .filter(Student.building == building, Student.room == room, Student.status == "离校")
        .all()
    )
    off_campus_ids = [s.student_id for s in off_campus]
    off_campus_records = {
        r.student_id: r
        for r in db.query(CheckRecord)
        .filter(
            CheckRecord.check_date == date,
            CheckRecord.student_id.in_(off_campus_ids),
        )
        .all()
    }
    off_campus_students = []
    for s in off_campus:
        rec = off_campus_records.get(s.student_id)
        off_campus_students.append(OffCampusStudent(
            student_id=s.student_id,
            name=s.name,
            is_present=rec.is_present if rec else None,
        ))

    return ApiResponse(
        data=RoomDetailResponse(
            room=room,
            expected_students=expected_students,
            off_campus_students=off_campus_students,
        ).model_dump()
    )


@router.post("/submit", response_model=ApiResponse)
def submit_check(
    body: SubmitRequest,
    db=Depends(get_db),
    user: dict = Depends(get_checker_user),
):
    username = user["sub"]
    u = db.get(User, username)
    building = u.assigned_building
    checker = u.name

    anomalies = 0
    for rec in body.records:
        student = db.get(Student, rec.student_id)
        if not student:
            continue

        status_snapshot = student.status
        anomaly_type = determine_anomaly(status_snapshot, rec.is_present)
        if anomaly_type:
            anomalies += 1

        # 覆盖式提交（唯一约束：check_date + student_id）
        existing = (
            db.query(CheckRecord)
            .filter(
                CheckRecord.check_date == body.date,
                CheckRecord.student_id == rec.student_id,
            )
            .first()
        )
        if existing:
            existing.is_present = rec.is_present
            existing.status_snapshot = status_snapshot
            existing.anomaly_type = anomaly_type
            existing.checker = checker
            existing.submitted_at = datetime.utcnow()
        else:
            db.add(
                CheckRecord(
                    check_date=body.date,
                    building=building,
                    room=body.room,
                    student_id=rec.student_id,
                    status_snapshot=status_snapshot,
                    is_present=rec.is_present,
                    anomaly_type=anomaly_type,
                    checker=checker,
                    submitted_at=datetime.utcnow(),
                )
            )

    db.commit()
    return ApiResponse(data=SubmitResponse(submitted=len(body.records), anomalies=anomalies).model_dump())


@router.post("/finish", response_model=ApiResponse)
def finish_check(
    date: date,
    db=Depends(get_db),
    user: dict = Depends(get_checker_user),
):
    # 检查是否所有楼栋都完成了
    total_buildings = 5  # 已知 5 栋楼
    checked_buildings = (
        db.query(CheckRecord.building)
        .filter(CheckRecord.check_date == date)
        .distinct()
        .all()
    )
    all_done = len(checked_buildings) >= total_buildings
    return ApiResponse(data=FinishResponse(all_buildings_done=all_done).model_dump())
