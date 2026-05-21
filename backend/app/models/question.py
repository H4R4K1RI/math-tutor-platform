from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from app.db.database import Base

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # single, multiple, open, number, match, order
    points = Column(Float, default=1)
    order = Column(Integer, default=0)
    
    # Для открытых вопросов (ключ для сравнения)
    correct_answer = Column(Text, nullable=True)