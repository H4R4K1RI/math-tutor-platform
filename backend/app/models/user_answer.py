from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, Float
from app.db.database import Base

class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_test_id = Column(Integer, ForeignKey("user_tests.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    answer = Column(Text, nullable=True)  # JSON для множественного выбора
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Float, default=0)