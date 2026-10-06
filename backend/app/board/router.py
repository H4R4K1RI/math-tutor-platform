from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.board.schemas import BoardResponse, BoardUpdate
from app.board.service import BoardsService
from app.shared.db import get_db

router = APIRouter(prefix="/board", tags=["board"])


@router.get("/{lesson_id}", response_model=BoardResponse)
async def get_board(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить состояние доски урока.

    Создаёт пустую доску, если её ещё нет.
    """
    service = BoardsService(db)
    return await service.get_or_create(lesson_id, current_user)


@router.put("/{lesson_id}", response_model=BoardResponse)
async def update_board(
    lesson_id: int,
    data: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновить состояние доски урока."""
    service = BoardsService(db)
    return await service.update(lesson_id, data.state, current_user)


@router.delete("/{lesson_id}", response_model=BoardResponse)
async def clear_board(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Очистить доску урока."""
    service = BoardsService(db)
    return await service.clear(lesson_id, current_user)