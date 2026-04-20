from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, delete
from typing import List, Optional

from app.db.database import get_db
from app.models.user import User
from app.models.assignment import Assignment
from app.models.chat import Chat, Message
from app.schemas.chat import ChatResponse, MessageResponse, ChatCreate
from app.core.dependencies import get_current_user
from app.socket_manager import sio

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
    chat_data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"Received student_id: {chat_data.student_id}, type: {type(chat_data.student_id)}")
    print(f"Current user: {current_user.id}, role: {current_user.role}")
    
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create chats")

    result = await db.execute(
        select(Chat).where(
            (Chat.teacher_id == current_user.id) &
            (Chat.student_id == chat_data.student_id)
        )
    )
    existing_chat = result.scalar_one_or_none()

    if existing_chat:
        return {"chat_id": existing_chat.id}

    new_chat = Chat(
        teacher_id=current_user.id,
        student_id=chat_data.student_id,
        assignment_id=chat_data.assignment_id
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

@router.get("/assignment/{assignment_id}")
async def get_or_create_chat_by_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить или создать чат, привязанный к заданию"""
    
    from app.models.assignment import Assignment
    
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if current_user.role == "teacher":
        student_id = assignment.student_id
        teacher_id = current_user.id
    else:
        student_id = current_user.id
        teacher_id = assignment.teacher_id
    
    if not student_id:
        raise HTTPException(status_code=400, detail="Assignment not assigned to specific student")
    
    result = await db.execute(
        select(Chat).where(
            (Chat.teacher_id == teacher_id) &
            (Chat.student_id == student_id) &
            (Chat.assignment_id == assignment_id)
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        chat = Chat(
            teacher_id=teacher_id,
            student_id=student_id,
            assignment_id=assignment_id
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
    
    return {"chat_id": chat.id}

@router.delete("/{chat_id}/messages")
async def clear_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Очистить историю сообщений в чате"""
    
    # Проверяем доступ к чату
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Удаляем все сообщения
    await db.execute(delete(Message).where(Message.chat_id == chat_id))
    await db.commit()
    
    # Обновляем updated_at
    await db.execute(update(Chat).where(Chat.id == chat_id).values(updated_at=func.now()))
    await db.commit()
    
    # Оповещаем участников через WebSocket
    await sio.emit('chat_cleared', {'chat_id': chat_id}, room=f"chat_{chat_id}")
    
    return {"message": "Chat history cleared"}

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Полностью удалить чат"""
    
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Удаляем чат (сообщения удалятся каскадно)
    await db.delete(chat)
    await db.commit()
    
    # Оповещаем участников
    await sio.emit('chat_deleted', {'chat_id': chat_id}, room=f"chat_{chat_id}")
    
    return {"message": "Chat deleted"}

@router.put("/messages/{message_id}")
async def edit_message(
    message_id: int,
    new_message: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Редактирование сообщения (только автор)"""
    
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own messages")
    
    message.message = new_message
    await db.commit()
    
    # Оповещаем участников чата
    await sio.emit('message_edited', {
        'message_id': message_id,
        'new_message': new_message,
        'chat_id': message.chat_id
    }, room=f"chat_{message.chat_id}")
    
    return {"message": "Message updated"}

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление сообщения (автор или учитель)"""
    
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Проверяем, кто может удалить
    chat_result = await db.execute(select(Chat).where(Chat.id == message.chat_id))
    chat = chat_result.scalar_one_or_none()
    
    if message.sender_id != current_user.id and current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="You don't have permission to delete this message")
    
    await db.delete(message)
    await db.commit()
    
    # Оповещаем участников чата
    await sio.emit('message_deleted', {
        'message_id': message_id,
        'chat_id': message.chat_id
    }, room=f"chat_{message.chat_id}")
    
    return {"message": "Message deleted"}

@router.get("/{chat_id}/search")
async def search_messages(
    chat_id: int,
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Поиск сообщений в чате по тексту"""
    
    # Проверяем доступ к чату
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Поиск сообщений
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .where(Message.message.ilike(f"%{q}%"))
        .order_by(Message.created_at)
        .limit(50)
    )
    messages = result.scalars().all()
    
    return messages
