from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class TutoringRequestCreate(BaseModel):
    teacher_id: int
    message: Optional[str] = None


class TutoringRequestUpdate(BaseModel):
    status: Literal["approved", "rejected"]


class TutoringRequestResponse(BaseModel):
    id: int
    teacher_id: int
    student_id: int
    student_name: Optional[str] = None
    teacher_name: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)