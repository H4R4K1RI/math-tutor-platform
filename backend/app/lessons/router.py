from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.lessons.schemas import (
    LessonCreate,
    LessonRequestCreate,
    LessonRequestResponse,
    LessonRequestUpdate,
    LessonResponse,
    LessonUpdate,
)
from app.lessons.service import LessonRequestsService, LessonsService
from app.shared.db import get_db

router = APIRouter(tags=["lessons"])


# ==================== LESSONS ====================


@router.post("/lessons/", response_model=LessonResponse)
async def create_lesson(
    lesson_data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создать урок (только учитель)."""
    service = LessonsService(db)
    return await service.create_lesson(lesson_data, current_user)


@router.get("/lessons/", response_model=List[LessonResponse])
async def get_lessons(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить уроки пользователя."""
    service = LessonsService(db)
    return await service.get_lessons(
        current_user, start_date, end_date, status
    )


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить урок (только учитель)."""
    service = LessonsService(db)
    return await service.update_lesson(lesson_id, lesson_data, current_user)


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отменить урок (с возвратом денег)."""
    service = LessonsService(db)
    return await service.delete_lesson(lesson_id, current_user)


# ==================== LESSON REQUESTS ====================


@router.post(
    "/lesson-requests/", response_model=LessonRequestResponse
)
async def create_lesson_request(
    request_data: LessonRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создать заявку на урок (только ученик)."""
    service = LessonRequestsService(db)
    return await service.create_request(request_data, current_user)


@router.get(
    "/lesson-requests/", response_model=List[LessonRequestResponse]
)
async def get_lesson_requests(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить заявки на урок."""
    service = LessonRequestsService(db)
    return await service.get_requests(current_user, status)


@router.put("/lesson-requests/{request_id}")
async def update_lesson_request(
    request_id: int,
    update_data: LessonRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Подтвердить или отклонить заявку (только учитель)."""
    service = LessonRequestsService(db)
    return await service.update_request(request_id, update_data, current_user)