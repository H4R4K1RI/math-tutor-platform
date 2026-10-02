from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)
    role: str = Field(default="student", pattern="^(student|teacher)$")
    invite_code: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    avatar: Optional[str] = None
    about: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[int] = 0
    total_students: Optional[int] = 0
    total_lessons: Optional[int] = 0
    rating: Optional[float] = 0

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    about: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[int] = None