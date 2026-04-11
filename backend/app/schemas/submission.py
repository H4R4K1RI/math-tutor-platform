from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SubmissionBase(BaseModel):
    content: Optional[str] = None
    files: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    assignment_id: int

class SubmissionUpdate(BaseModel):
    content: Optional[str] = None  
    files: Optional[str] = None
    status: Optional[str] = None
    feedback: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: int
    content: Optional[str] = None  # Явно добавляем content
    files: Optional[str] = None
    status: str
    feedback: Optional[str] = None
    assignment_id: int
    student_id: int
    submitted_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SubmissionListResponse(BaseModel):
    id: int
    content: Optional[str] = None  # Явно добавляем content
    files: Optional[str] = None  # Добавить
    feedback: Optional[str] = None  # Добавить
    status: str
    assignment_id: int
    student_id: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True