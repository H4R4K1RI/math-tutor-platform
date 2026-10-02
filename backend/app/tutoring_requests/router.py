from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.shared.db import get_db
from app.tutoring_requests.schemas import (
    TutoringRequestCreate,
    TutoringRequestResponse,
    TutoringRequestUpdate,
)
from app.tutoring_requests.service import TutoringRequestsService

router = APIRouter(prefix="/tutoring-requests", tags=["tutoring-requests"])


@router.post("/", response_model=TutoringRequestResponse)
async def create_tutoring_request(
    data: TutoringRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ученик отправляет заявку на обучение учителю."""
    service = TutoringRequestsService(db)
    return await service.create_request(data, current_user)


@router.get("/", response_model=List[TutoringRequestResponse])
async def get_tutoring_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список заявок."""
    service = TutoringRequestsService(db)
    return await service.get_requests(current_user)


@router.get("/check/{teacher_id}")
async def check_connection_status(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Проверить статус связи ученика с учителем."""
    service = TutoringRequestsService(db)
    return await service.check_connection_status(teacher_id, current_user)


@router.put("/{request_id}")
async def update_tutoring_request(
    request_id: int,
    data: TutoringRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Принять или отклонить заявку (только учитель)."""
    service = TutoringRequestsService(db)
    return await service.update_request(request_id, data, current_user)