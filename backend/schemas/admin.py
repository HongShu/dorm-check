from pydantic import BaseModel, Field
from datetime import date, datetime


class BuildingProgress(BaseModel):
    building: int
    checked_rooms: int
    total_rooms: int
    finished_at: datetime | None = None


class AnomalySummary(BaseModel):
    total: int
    missing: int
    unreported_return: int


class DashboardResponse(BaseModel):
    buildings: list[BuildingProgress]
    anomaly_summary: AnomalySummary


class AnomalyItem(BaseModel):
    date: date
    building: int
    room: str
    student_id: str
    name: str
    counselor: str
    anomaly_type: str
    checker: str
    submitted_at: datetime


class AnomaliesResponse(BaseModel):
    items: list[AnomalyItem]


class ReportResponse(BaseModel):
    report: str
    generated_at: datetime | None = None


class GenerateReportRequest(BaseModel):
    date: date


class ImportResponse(BaseModel):
    imported: int
    by_building: dict[int, int]


class ResetCheckerPasswordsRequest(BaseModel):
    new_password: str = Field(..., min_length=4, max_length=50)


class ResetPasswordsResponse(BaseModel):
    updated_count: int


class UserItem(BaseModel):
    username: str
    name: str
    role: str
    assigned_building: int | None = None


class UsersResponse(BaseModel):
    users: list[UserItem]
