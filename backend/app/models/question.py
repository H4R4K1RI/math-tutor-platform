from app.shared.db import Base
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(
        Integer,
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    points = Column(Float, default=1)
    order = Column(Integer, default=0)
    correct_answer = Column(Text, nullable=True)