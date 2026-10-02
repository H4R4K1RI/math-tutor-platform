from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.chat.schemas import ChatCreate
from app.chat.service import ChatsService
from app.shared.db import get_db

router = APIRouter(prefix="/chats", tags=["chats"])


# ==================== СПЕЦИФИЧНЫЕ (до /{chat_id}) ====================


@router.get("/")
async def get_chats(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список чатов пользователя с пагинацией."""
    service = ChatsService(db)
    return await service.get_chats(current_user, skip, limit)


@router.post("/")
async def create_chat(
    chat_data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создать чат (только для учителя, только с учеником)."""
    service = ChatsService(db)
    return await service.create_chat(chat_data, current_user)


@router.get("/student/{student_id}")
async def get_or_create_chat_with_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить или создать чат с учеником (для учителя)."""
    service = ChatsService(db)
    return await service.get_or_create_by_student(student_id, current_user)


@router.get("/assignment/{assignment_id}")
async def get_or_create_chat_by_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить или создать чат, привязанный к заданию."""
    service = ChatsService(db)
    return await service.get_or_create_by_assignment(assignment_id, current_user)


@router.put("/messages/{message_id}")
async def edit_message(
    message_id: int,
    new_message: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Редактирование сообщения (только автор)."""
    service = ChatsService(db)
    return await service.edit_message(message_id, new_message, current_user)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление сообщения (автор или учитель этого чата)."""
    service = ChatsService(db)
    return await service.delete_message(message_id, current_user)


# ==================== ОБЩИЕ (/{chat_id}) ====================


@router.get("/{chat_id}")
async def get_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Информация о конкретном чате (только для участников)."""
    service = ChatsService(db)
    return await service.get_chat(chat_id, current_user)


@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: int,
    limit: int = 500,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """История сообщений чата."""
    service = ChatsService(db)
    return await service.get_messages(chat_id, current_user, limit, offset)


@router.get("/{chat_id}/search")
async def search_messages(
    chat_id: int,
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Поиск сообщений в чате по тексту."""
    service = ChatsService(db)
    return await service.search_messages(chat_id, q, current_user)


@router.delete("/{chat_id}/messages")
async def clear_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Очистить историю сообщений в чате."""
    service = ChatsService(db)
    return await service.clear_messages(chat_id, current_user)


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Полностью удалить чат."""
    service = ChatsService(db)
    return await service.delete_chat(chat_id, current_user)