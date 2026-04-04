from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    attachments = Column(Text, nullable=True)  # JSON строка со ссылками на файлы
    due_date = Column(DateTime(timezone=True), nullable=False)
    
    # Связь с учителем (кто создал)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Связь с учеником (для кого задание)
    # NULL значит для всех учеников
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())