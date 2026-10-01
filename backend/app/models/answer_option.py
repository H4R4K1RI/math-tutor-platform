from app.db.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, default=0)