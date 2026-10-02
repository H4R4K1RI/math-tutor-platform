from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.shared.db import Base


class TutoringRequest(Base):
    __tablename__ = "tutoring_requests"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    message = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_tutoring_requests_teacher_id", "teacher_id"),
        Index("idx_tutoring_requests_student_id", "student_id"),
        Index("idx_tutoring_requests_status", "status"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_tutoring_request_status",
        ),
    )