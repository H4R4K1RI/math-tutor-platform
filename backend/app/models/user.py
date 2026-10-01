from app.db.database import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="student", nullable=False)
    is_active = Column(Boolean, default=True)
    avatar = Column(String(500), nullable=True)
    about = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    experience_years = Column(Integer, default=0)
    total_students = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)
    rating = Column(Float, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "role IN ('teacher', 'student')",
            name="ck_user_role",
        ),
    )