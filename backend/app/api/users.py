from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.dependencies import get_current_user, get_current_teacher

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/students", response_model=list[UserResponse])
async def get_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить список всех учеников (только для учителя)"""
    result = await db.execute(
        select(User).where(User.role == "student")
    )
    students = result.scalars().all()
    return students

@router.put("/profile")
async def update_profile(
    profile_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    """Получить публичный профиль репетитора"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    tutor = result.scalar_one_or_none()
    
    if not tutor or tutor.role != "teacher":
        raise HTTPException(status_code=404, detail="Tutor not found")
    
    # Подсчитываем реальную статистику
    students_result = await db.execute(
        select(func.count(StudentProgress.id))
        .where(StudentProgress.teacher_id == user_id)
    )
    total_students = students_result.scalar() or 0
    
    lessons_result = await db.execute(
        select(func.count(Submission.id))
        .where(Submission.student_id.in_(
            select(StudentProgress.student_id).where(StudentProgress.teacher_id == user_id)
        ))
    )
    total_lessons = lessons_result.scalar() or 0
    
    return {
        "id": tutor.id,
        "full_name": tutor.full_name,
        "avatar": tutor.avatar,
        "about": tutor.about,
        "education": tutor.education,
        "experience_years": tutor.experience_years,
        "rating": tutor.rating or 4.5,
        "total_students": total_students,
        "total_lessons": total_lessons,
        "subjects": []  # позже добавим предметы
    }