from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    Text,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.shared.db import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(
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
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tutor_id", "student_id", name="uq_review_tutor_student"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
    )