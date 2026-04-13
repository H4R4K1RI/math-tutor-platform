from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from typing import List, Optional

from app.db.database import get_db
from app.models.user import User
from app.models.assignment import Assignment
from app.models.chat import Chat, Message
from app.schemas.chat import ChatResponse, MessageResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/chats", tags=["chats"])

@router.get("/")
async def get_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список чатов пользователя"""
    
    if current_user.role == "teacher":
        result = await db.execute(
            select(Chat)
            .where(Chat.teacher_id == current_user.id)
            .order_by(desc(Chat.updated_at))
        )
    else:
        result = await db.execute(
            select(Chat)
            .where(Chat.student_id == current_user.id)
            .order_by(desc(Chat.updated_at))
        )
    
    chats = result.scalars().all()
    
    response = []
    for chat in chats:
        last_msg_result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        last_message = last_msg_result.scalar_one_or_none()
        
        unread_result = await db.execute(
            select(func.count()).where(
                (Message.chat_id == chat.id) &
                (Message.sender_id != current_user.id) &
                (Message.is_read == False)
            )
        )
        unread_count = unread_result.scalar() or 0
        
        other_user_id = chat.teacher_id if current_user.id == chat.student_id else chat.student_id
        user_result = await db.execute(select(User).where(User.id == other_user_id))
        other_user = user_result.scalar_one_or_none()
        
        response.append({
            "id": chat.id,
            "other_user_id": other_user_id,
            "other_user_name": other_user.full_name if other_user else "Пользователь",
            "assignment_id": chat.assignment_id,
            "last_message": last_message.message if last_message else None,
            "last_message_time": last_message.created_at if last_message else None,
            "unread_count": unread_count,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at
        })
    
    return response

@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить историю сообщений чата"""
    
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if current_user.role != "teacher" and current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return messages

@router.post("/")
async def create_chat(
    student_id: int,
    assignment_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать новый чат (только для учителя)"""
    
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create chats")
    
    result = await db.execute(
        select(Chat).where(
            (Chat.teacher_id == current_user.id) &
            (Chat.student_id == student_id)
        )
    )
    existing_chat = result.scalar_one_or_none()
    
    if existing_chat:
        return {"chat_id": existing_chat.id}
    
    new_chat = Chat(
        teacher_id=current_user.id,
        student_id=student_id,
        assignment_id=assignment_id
    )
    
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    
    return {"chat_id": new_chat.id}

@router.get("/student/{student_id}")
async def get_or_create_chat_with_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить или создать чат с учеником (для учителя)"""
    
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create chats")
    
    result = await db.execute(
        select(Chat).where(
            (Chat.teacher_id == current_user.id) &
            (Chat.student_id == student_id)
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        chat = Chat(
            teacher_id=current_user.id,
            student_id=student_id,
            assignment_id=None
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
    
    return {"chat_id": chat.id}