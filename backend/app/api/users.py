from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.shared.db import get_db
from app.models.assignment import Assignment
from app.models.chat import Chat
from app.models.lesson import Lesson
from app.models.review import Review
from app.auth.models import User
from app.auth.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/students", response_model=list[UserResponse])
async def get_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить список учеников учителя (только связанных с ним)"""

    from app.api.students import get_teacher_student_ids

    student_ids = await get_teacher_student_ids(db, current_user.id)

    if not student_ids:
        return []

    result = await db.execute(select(User).where(User.id.in_(student_ids)))
    students = result.scalars().all()
    return students


@router.put("/profile")
async def update_profile(
    profile_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновить профиль пользователя"""

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

    await db.commit()
    await db.refresh(current_user)

    return {"message": "Profile updated"}


@router.get("/tutor/{user_id}")
async def get_tutor_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Получить публичный профиль репетитора (доступен без авторизации)"""

    result = await db.execute(select(User).where(User.id == user_id))
    tutor = result.scalar_one_or_none()

    if not tutor or tutor.role != "teacher":
        raise HTTPException(status_code=404, detail="Tutor not found")

    students_result = await db.execute(
        select(func.count(func.distinct(Assignment.student_id))).where(
            Assignment.teacher_id == user_id,
            Assignment.student_id.isnot(None),
        )
    )
    total_students = students_result.scalar() or 0

    lessons_result = await db.execute(
        select(func.count(Lesson.id)).where(
            Lesson.teacher_id == user_id,
            Lesson.status == "completed",
        )
    )
    total_lessons = lessons_result.scalar() or 0

    rating_result = await db.execute(
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


@router.get("/teachers", response_model=list[UserResponse])
async def get_teachers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список учителей.

    Для ученика — только те, с кем он связан (есть чат).
    Для учителя — все учителя.
    """
    if current_user.role == "student":
        result = await db.execute(
            select(User)
            .join(Chat, Chat.teacher_id == User.id)
            .where(Chat.student_id == current_user.id)
            .where(User.role == "teacher")
            .distinct()
        )
        teachers = result.scalars().all()
    else:
        result = await db.execute(select(User).where(User.role == "teacher"))
        teachers = result.scalars().all()

    return teachers