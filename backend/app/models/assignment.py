from app.shared.db import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    attachments = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)

    teacher_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    student_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    group_id = Column(
        Integer,
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())