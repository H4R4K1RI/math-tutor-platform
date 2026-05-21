from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.db.database import Base

class AnswerOption(Base):
    __tablename__ = "answer_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, default=0)