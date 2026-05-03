from pydantic import BaseModel
from datetime import date, datetime


class RoomCard(BaseModel):
    room: str
    expected_count: int
    checked: bool
    anomaly_count: int
    checked_at: datetime | None = None


class RoomsResponse(BaseModel):
    building: int
    date: date
    rooms: list[RoomCard]


class StudentInfo(BaseModel):
    student_id: str
    name: str
    is_present: bool | None = None


class OffCampusStudent(BaseModel):
    student_id: str
    name: str
    is_present: bool | None = None


class RoomDetailResponse(BaseModel):
    room: str
    expected_students: list[StudentInfo]
    off_campus_students: list[OffCampusStudent]


class RecordItem(BaseModel):
    student_id: str
    is_present: bool


class SubmitRequest(BaseModel):
    date: date
    room: str
    records: list[RecordItem]


class SubmitResponse(BaseModel):
    submitted: int
    anomalies: int


class FinishResponse(BaseModel):
    all_buildings_done: bool
