from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Student(Base):
    __tablename__ = "student"

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    counselor: Mapped[str] = mapped_column(String(100), nullable=False)
    building: Mapped[int] = mapped_column(Integer, nullable=False)
    room: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
