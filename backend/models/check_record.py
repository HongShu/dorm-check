from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, DateTime, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class CheckRecord(Base):
    __tablename__ = "check_record"
    __table_args__ = (
        UniqueConstraint("check_date", "student_id", name="uix_check_date_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    building: Mapped[int] = mapped_column(Integer, nullable=False)
    room: Mapped[str] = mapped_column(String(20), nullable=False)
    student_id: Mapped[str] = mapped_column(String(20), nullable=False)
    status_snapshot: Mapped[str] = mapped_column(String(20), nullable=False)
    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    anomaly_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    checker: Mapped[str] = mapped_column(String(100), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
