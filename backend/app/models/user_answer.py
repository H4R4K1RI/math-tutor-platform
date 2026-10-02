from app.shared.db import Base
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, Text


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_test_id = Column(
        Integer,
        ForeignKey("user_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Float, default=0)