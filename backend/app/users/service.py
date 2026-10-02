from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserUpdate
from app.assignments.models import Assignment
from app.chat.models import Chat
from app.models.lesson import Lesson
from app.models.review import Review


class UsersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_students(self, teacher_id: int) -> list[User]:
        """Список учеников учителя (только связанных с ним)."""
        from app.students.service import get_teacher_student_ids

        student_ids = await get_teacher_student_ids(self.db, teacher_id)

        if not student_ids:
            return []

        result = await self.db.execute(
            select(User).where(User.id.in_(student_ids))
        )
        return list(result.scalars().all())

    async def update_profile(
        self, current_user: User, profile_data: UserUpdate
    ) -> User:
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name
        if profile_data.avatar is not None:
            current_user.avatar = profile_data.avatar
        if profile_data.about is not None:
            current_user.about = profile_data.about
        if profile_data.education is not None:
            current_user.education = profile_data.education
        if profile_data.experience_years is not None:
            current_user.experience_years = profile_data.experience_years

        await self.db.commit()
        await self.db.refresh(current_user)
        return current_user

    async def get_tutor_profile(self, user_id: int) -> dict:
        result = await self.db.execute(select(User).where(User.id == user_id))
        tutor = result.scalar_one_or_none()

        if not tutor or tutor.role != "teacher":
            raise HTTPException(status_code=404, detail="Tutor not found")

        students_result = await self.db.execute(
            select(func.count(func.distinct(Assignment.student_id))).where(
                Assignment.teacher_id == user_id,
                Assignment.student_id.isnot(None),
            )
        )
        total_students = students_result.scalar() or 0

        lessons_result = await self.db.execute(
            select(func.count(Lesson.id)).where(
                Lesson.teacher_id == user_id,
                Lesson.status == "completed",
            )
        )
        total_lessons = lessons_result.scalar() or 0

        rating_result = await self.db.execute(
            select(func.avg(Review.rating)).where(Review.tutor_id == user_id)
        )
        avg_rating = rating_result.scalar() or 0

        return {
            "id": tutor.id,
            "full_name": tutor.full_name,
            "avatar": tutor.avatar,
            "about": tutor.about,
            "education": tutor.education,
            "experience_years": tutor.experience_years,
            "rating": round(avg_rating, 1),
            "total_students": total_students,
            "total_lessons": total_lessons,
            "subjects": [],
        }

    async def get_teachers(self, current_user: User) -> list[User]:
        """Для ученика — только связанные; для учителя — все."""
        if current_user.role == "student":
            result = await self.db.execute(
                select(User)
                .join(Chat, Chat.teacher_id == User.id)
                .where(Chat.student_id == current_user.id)
                .where(User.role == "teacher")
                .distinct()
            )
        else:
            result = await self.db.execute(
                select(User).where(User.role == "teacher")
            )
        return list(result.scalars().all())