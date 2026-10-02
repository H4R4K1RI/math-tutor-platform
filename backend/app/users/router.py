from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.auth.schemas import UserResponse, UserUpdate
from app.shared.db import get_db
from app.users.service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/students", response_model=list[UserResponse])
async def get_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Список учеников учителя (только связанных с ним)."""
    service = UsersService(db)
    return await service.get_students(current_user.id)


@router.put("/profile")
async def update_profile(
    profile_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновить профиль пользователя."""
    service = UsersService(db)
    await service.update_profile(current_user, profile_data)
    return {"message": "Profile updated"}


@router.get("/tutor/{user_id}")
async def get_tutor_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Публичный профиль репетитора (доступен без авторизации)."""
    service = UsersService(db)
    return await service.get_tutor_profile(user_id)


@router.get("/teachers", response_model=list[UserResponse])
async def get_teachers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список учителей (для ученика — только связанные)."""
    service = UsersService(db)
    return await service.get_teachers(current_user)