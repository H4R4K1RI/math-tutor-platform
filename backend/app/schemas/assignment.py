from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    attachments: Optional[str] = None
    due_date: datetime
    student_id: Optional[int] = None  # Если None — задание для всех

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    attachments: Optional[str] = None
    due_date: Optional[datetime] = None
    student_id: Optional[int] = None

class AssignmentResponse(AssignmentBase):
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AssignmentListResponse(BaseModel):
    id: int
    title: str
    due_date: datetime
    teacher_id: int
    student_id: Optional[int] = None
    
    class Config:
        from_attributes = True