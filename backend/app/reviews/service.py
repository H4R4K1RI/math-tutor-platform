from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.lessons.models import Lesson
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate


class ReviewsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== CREATE ====================

    async def create_review(
        self, tutor_id: int, data: ReviewCreate, current_user: User
    ) -> dict:
        """Оставить отзыв репетитору (только ученик)."""

        if current_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can leave reviews",
            )

        tutor_result = await self.db.execute(
            select(User).where(User.id == tutor_id, User.role == "teacher")
        )
        tutor = tutor_result.scalar_one_or_none()
        if not tutor:
            raise HTTPException(status_code=404, detail="Tutor not found")

        if current_user.id == tutor_id:
            raise HTTPException(
                status_code=400, detail="You cannot review yourself"
            )

        if data.lesson_id:
            lesson_result = await self.db.execute(
                select(Lesson).where(
                    Lesson.id == data.lesson_id,
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

        existing_result = await self.db.execute(
            select(Review).where(
                Review.tutor_id == tutor_id,
                Review.student_id == current_user.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="You have already reviewed this tutor",
            )

        new_review = Review(
            tutor_id=tutor_id,
            student_id=current_user.id,
            lesson_id=data.lesson_id,
            rating=data.rating,
            comment=data.comment,
        )

        self.db.add(new_review)
        await self.db.commit()
        await self.db.refresh(new_review)

        rating_result = await self.db.execute(
            select(func.avg(Review.rating)).where(Review.tutor_id == tutor_id)
        )
        avg_rating = rating_result.scalar() or 0

        await self.db.execute(
            update(User).where(User.id == tutor_id).values(rating=avg_rating)
        )
        await self.db.commit()

        return {
            "message": "Review created",
            "new_average_rating": avg_rating,
        }

    # ==================== LIST ====================

    async def get_tutor_reviews(
        self, tutor_id: int, skip: int = 0, limit: int = 20
    ) -> list[dict]:
        """Список отзывов о репетиторе."""

        result = await self.db.execute(
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
        students_result = await self.db.execute(
            select(User).where(User.id.in_(student_ids))
        )
        students_map = {u.id: u for u in students_result.scalars().all()}

        response = []
        for review in reviews:
            student = students_map.get(review.student_id)
            response.append(
                {
                    "id": review.id,
                    "student_id": review.student_id,
                    "student_name": (
                        student.full_name if student else "Unknown"
                    ),
                    "rating": review.rating,
                    "comment": review.comment,
                    "created_at": review.created_at,
                }
            )

        return response

    # ==================== RATING ====================

    async def get_tutor_rating(self, tutor_id: int) -> dict:
        """Средний рейтинг репетитора."""

        result = await self.db.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(
                Review.tutor_id == tutor_id
            )
        )
        avg_rating, total_reviews = result.first()

        return {
            "average_rating": round(avg_rating or 0, 1),
            "total_reviews": total_reviews or 0,
        }