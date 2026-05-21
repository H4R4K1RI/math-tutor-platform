from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="student", nullable=False)  # Изменено: String вместо Enum
    is_active = Column(Boolean, default=True)
    avatar = Column(String(500), nullable=True)  # URL аватара
    about = Column(Text, nullable=True)  # О себе
    education = Column(Text, nullable=True)  # Образование
    experience_years = Column(Integer, default=0)  # Опыт в годах
    total_students = Column(Integer, default=0)  # Всего учеников
    total_lessons = Column(Integer, default=0)  # Всего уроков
    rating = Column(Float, default=0)  # Рейтинг
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    
