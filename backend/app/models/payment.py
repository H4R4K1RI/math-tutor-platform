from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.sql import func
from app.shared.db import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    teacher_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount = Column(Numeric(10, 2), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StudentBalance(Base):
    __tablename__ = "student_balances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    teacher_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    balance = Column(Numeric(10, 2), default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "student_id", "teacher_id", name="uq_student_balance_student_teacher"
        ),
        Index("idx_student_balances_teacher_id", "teacher_id"),
    )