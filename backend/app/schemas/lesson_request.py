from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Literal, Optional


class LessonRequestCreate(BaseModel):
    teacher_id: int
    title: Optional[str] = None
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class LessonRequestUpdate(BaseModel):
    status: Literal["approved", "rejected"]
    price: Optional[Decimal] = Field(default=Decimal("0"), ge=0)


class LessonRequestResponse(BaseModel):
    id: int
    teacher_id: int
    student_id: int
    student_name: Optional[str] = None
    title: Optional[str]
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)