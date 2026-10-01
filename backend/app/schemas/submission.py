from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class SubmissionBase(BaseModel):
    content: Optional[str] = None
    files: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    assignment_id: int


class SubmissionUpdate(BaseModel):
    content: Optional[str] = None
    files: Optional[str] = None
    status: Optional[Literal["pending", "approved", "rejected"]] = None
    feedback: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: int
    content: Optional[str] = None
    files: Optional[str] = None
    status: str
    feedback: Optional[str] = None
    assignment_id: int
    student_id: int
    submitted_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)