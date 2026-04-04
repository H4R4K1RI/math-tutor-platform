from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SubmissionBase(BaseModel):
    content: Optional[str] = None
    files: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    assignment_id: int

class SubmissionUpdate(BaseModel):
    status: Optional[str] = None  
    feedback: Optional[str] = None

class SubmissionResponse(SubmissionBase):
    id: int
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
    status: str  
    assignment_id: int
    student_id: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True