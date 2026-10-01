from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    lesson_id: Optional[int] = None


class ReviewResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TutorRatingResponse(BaseModel):
    average_rating: float
    total_reviews: int