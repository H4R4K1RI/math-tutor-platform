from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.auth.dependencies import get_current_user
from app.shared.db import get_db
from app.lessons.models import Lesson
from app.models.review import Review
from app.auth.models import User
from app.schemas.review import ReviewCreate, ReviewResponse, TutorRatingResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/tutor/{tutor_id}")
async def create_review(
    tutor_id: int,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Оставить отзыв репетитору (только ученик)"""

    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can leave reviews")

    tutor_result = await db.execute(
        select(User).where(User.id == tutor_id, User.role == "teacher")
    )
    tutor = tutor_result.scalar_one_or_none()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    if current_user.id == tutor_id:
        raise HTTPException(status_code=400, detail="You cannot review yourself")

    if review_data.lesson_id:
        lesson_result = await db.execute(
            select(Lesson).where(
                Lesson.id == review_data.lesson_id,
                Lesson.student_id == current_user.id,
                Lesson.teacher_id == tutor_id,
                Lesson.status == "completed",
            )
        )
        lesson = lesson_result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(
                status_code=400,
                detail="You can only review completed lessons with this tutor",
            )

    existing_result = await db.execute(
        select(Review).where(
            Review.tutor_id == tutor_id,
            Review.student_id == current_user.id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, detail="You have already reviewed this tutor"
        )

    new_review = Review(
        tutor_id=tutor_id,
        student_id=current_user.id,
        lesson_id=review_data.lesson_id,
        rating=review_data.rating,
        comment=review_data.comment,
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    rating_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.tutor_id == tutor_id)
    )
    avg_rating = rating_result.scalar() or 0

    await db.execute(update(User).where(User.id == tutor_id).values(rating=avg_rating))
    await db.commit()

    return {"message": "Review created", "new_average_rating": avg_rating}


@router.get("/tutor/{tutor_id}", response_model=List[ReviewResponse])
async def get_tutor_reviews(
    tutor_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Получить все отзывы о репетиторе (оптимизировано)"""

    result = await db.execute(
        select(Review)
        .where(Review.tutor_id == tutor_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    reviews = result.scalars().all()

    if not reviews:
        return []

    student_ids = {r.student_id for r in reviews}
    students_result = await db.execute(select(User).where(User.id.in_(student_ids)))
    students_map = {u.id: u for u in students_result.scalars().all()}

    response = []
    for review in reviews:
        student = students_map.get(review.student_id)
        response.append(
            {
                "id": review.id,
                "student_id": review.student_id,
                "student_name": student.full_name if student else "Unknown",
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
            }
        )

    return response


@router.get("/tutor/{tutor_id}/rating", response_model=TutorRatingResponse)
async def get_tutor_rating(
    tutor_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Получить средний рейтинг репетитора"""

    result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.tutor_id == tutor_id
        )
    )
    avg_rating, total_reviews = result.first()

    return {
        "average_rating": round(avg_rating or 0, 1),
        "total_reviews": total_reviews or 0,
    }