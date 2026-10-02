from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=1)
    attachments: Optional[str] = None
    due_date: datetime
    student_id: Optional[int] = None
    group_id: Optional[int] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    attachments: Optional[str] = None
    due_date: Optional[datetime] = None
    student_id: Optional[int] = None
    group_id: Optional[int] = None


class AssignmentResponse(AssignmentBase):
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    group_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AssignmentListResponse(BaseModel):
    id: int
    title: str
    description: str
    attachments: Optional[str] = None
    due_date: datetime
    teacher_id: int
    student_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


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