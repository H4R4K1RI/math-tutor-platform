from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.shared.db import Base


class SentReminder(Base):
    __tablename__ = "sent_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reminder_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "reminder_type",
            "entity_id",
            name="uq_sent_reminder",
        ),
    )