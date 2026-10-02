from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    DateTime,
    ForeignKey,
    String,
    Text,
    Numeric,
)
from sqlalchemy.sql import func
from app.shared.db import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    price = Column(Numeric(10, 2), default=0)
    status = Column(String(50), default="scheduled")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled')",
            name="ck_lesson_status",
        ),
        CheckConstraint("price >= 0", name="ck_lesson_price"),
    )