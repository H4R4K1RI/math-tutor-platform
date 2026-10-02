from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.reviews.schemas import (
    ReviewCreate,
    ReviewResponse,
    TutorRatingResponse,
)
from app.reviews.service import ReviewsService
from app.shared.db import get_db

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/tutor/{tutor_id}")
async def create_review(
    tutor_id: int,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Оставить отзыв репетитору (только ученик)."""
    service = ReviewsService(db)
    return await service.create_review(tutor_id, review_data, current_user)


@router.get("/tutor/{tutor_id}", response_model=List[ReviewResponse])
async def get_tutor_reviews(
    tutor_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Список отзывов о репетиторе."""
    service = ReviewsService(db)
    return await service.get_tutor_reviews(tutor_id, skip, limit)


@router.get(
    "/tutor/{tutor_id}/rating", response_model=TutorRatingResponse
)
async def get_tutor_rating(
    tutor_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Средний рейтинг репетитора."""
    service = ReviewsService(db)
    return await service.get_tutor_rating(tutor_id)