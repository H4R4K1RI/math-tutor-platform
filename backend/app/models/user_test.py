from app.shared.db import Base
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func


class UserTest(Base):
    __tablename__ = "user_tests"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(
        Integer,
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    status = Column(String(50), default="in_progress")

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed')",
            name="ck_user_test_status",
        ),
    )