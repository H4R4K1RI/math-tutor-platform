import json

from app.api.uploads import delete_file
from app.core.dependencies import get_current_user
from app.core.logger import logger
from app.db.database import get_db
from app.models.chat import Chat, Message
from app.models.user import User
from app.schemas.chat import ChatCreate
from app.socket_manager import sio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/")
async def get_chats(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список чатов пользователя с пагинацией (оптимизировано)"""

    if current_user.role == "teacher":
        query = (
            select(Chat)
            .where(Chat.teacher_id == current_user.id)
            .order_by(desc(Chat.updated_at))
        )
        total_query = (
            select(func.count())
            .where(Chat.teacher_id == current_user.id)
            .select_from(Chat)
        )
    else:
        query = (
            select(Chat)
            .where(Chat.student_id == current_user.id)
            .order_by(desc(Chat.updated_at))
        )
        total_query = (
            select(func.count())
            .where(Chat.student_id == current_user.id)
            .select_from(Chat)
        )

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset(skip).limit(limit))
    chats = result.scalars().all()

    if not chats:
        return {"items": [], "total": total, "skip": skip, "limit": limit}

    chat_ids = [chat.id for chat in chats]

    # Последние сообщения — одним запросом
    last_msg_subq = (
        select(
            Message.chat_id,
            func.max(Message.created_at).label("max_created"),
        )
        .where(Message.chat_id.in_(chat_ids))
        .group_by(Message.chat_id)
        .subquery()
    )

    last_msgs_result = await db.execute(
        select(Message).join(
            last_msg_subq,
            (Message.chat_id == last_msg_subq.c.chat_id)
            & (Message.created_at == last_msg_subq.c.max_created),
        )
    )
    last_messages = {m.chat_id: m for m in last_msgs_result.scalars().all()}

    # Непрочитанные — одним запросом
    unread_result = await db.execute(
        select(Message.chat_id, func.count(Message.id))
        .where(Message.chat_id.in_(chat_ids))
        .where(Message.sender_id != current_user.id)
        .where(Message.is_read == False)  # noqa: E712
        .group_by(Message.chat_id)
    )
    unread_counts = {row[0]: row[1] for row in unread_result.all()}

    # Другие пользователи — одним запросом
    other_user_ids = set()
    for chat in chats:
        if current_user.id == chat.student_id:
            other_user_ids.add(chat.teacher_id)
        else:
            other_user_ids.add(chat.student_id)

    users_result = await db.execute(select(User).where(User.id.in_(other_user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    response = []
    for chat in chats:
        other_user_id = (
            chat.teacher_id if current_user.id == chat.student_id else chat.student_id
        )
        other_user = users_map.get(other_user_id)

        last_message = last_messages.get(chat.id)
        unread_count = unread_counts.get(chat.id, 0)

        response.append(
            {
                "id": chat.id,
                "other_user_id": other_user_id,
                "other_user_name": (
                    other_user.full_name if other_user else "Пользователь"
                ),
                "assignment_id": chat.assignment_id,
                "last_message": last_message.message if last_message else None,
                "last_message_time": last_message.created_at if last_message else None,
                "unread_count": unread_count,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
            }
        )

    return {"items": response, "total": total, "skip": skip, "limit": limit}


@router.get("/{chat_id}")
async def get_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить информацию о конкретном чате (только для участников)"""

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")

    other_user_id = (
        chat.teacher_id if current_user.id == chat.student_id else chat.student_id
    )

    other_user_result = await db.execute(select(User).where(User.id == other_user_id))
    other_user = other_user_result.scalar_one_or_none()

    return {
        "id": chat.id,
        "teacher_id": chat.teacher_id,
        "student_id": chat.student_id,
        "other_user_id": other_user_id,
        "other_user_name": other_user.full_name if other_user else "Пользователь",
        "assignment_id": chat.assignment_id,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
    }


@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: int,
    limit: int = 500,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить историю сообщений чата"""

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in (chat.teacher_id, chat.student_id):
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
    current_user: User = Depends(get_current_user),
):
    """Создать чат (только для учителя, только с учеником)"""

    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create chats")

    student_result = await db.execute(
        select(User).where(User.id == chat_data.student_id, User.role == "student")
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    existing_chat_result = await db.execute(
        select(Chat).where(
            (Chat.teacher_id == current_user.id)
            & (Chat.student_id == chat_data.student_id)
        )
    )
    existing_chat = existing_chat_result.scalar_one_or_none()

    if existing_chat:
        return {"chat_id": existing_chat.id}

    from app.api.students import get_teacher_student_ids

    teacher_student_ids = await get_teacher_student_ids(db, current_user.id)

    if chat_data.student_id not in teacher_student_ids:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this student. Send an invitation first.",
        )

    new_chat = Chat(
        teacher_id=current_user.id,
        student_id=chat_data.student_id,
        assignment_id=chat_data.assignment_id,
    )

    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)

    return {"chat_id": new_chat.id}


@router.get("/student/{student_id}")
async def get_or_create_chat_with_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить или создать чат с учеником (для учителя)"""

    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create chats")

    student_result = await db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    result = await db.execute(
        select(Chat).where(
            (Chat.teacher_id == current_user.id) & (Chat.student_id == student_id)
        )
    )
    chat = result.scalar_one_or_none()

    if chat:
        return {"chat_id": chat.id}

    from app.api.students import get_teacher_student_ids

    teacher_student_ids = await get_teacher_student_ids(db, current_user.id)

    if student_id not in teacher_student_ids:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this student. Send an invitation first.",
        )

    chat = Chat(teacher_id=current_user.id, student_id=student_id, assignment_id=None)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    return {"chat_id": chat.id}


@router.get("/assignment/{assignment_id}")
async def get_or_create_chat_by_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить или создать чат, привязанный к заданию"""

    from app.models.assignment import Assignment

    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if current_user.role == "teacher":
        if assignment.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        student_id = assignment.student_id
        teacher_id = current_user.id
    else:
        if assignment.student_id == current_user.id:
            pass
        elif assignment.student_id is None:
            from app.api.assignments import _get_student_teacher_ids

            teacher_ids = await _get_student_teacher_ids(db, current_user.id)
            if assignment.teacher_id not in teacher_ids:
                raise HTTPException(status_code=403, detail="Access denied")
        else:
            raise HTTPException(status_code=403, detail="Access denied")

        student_id = current_user.id
        teacher_id = assignment.teacher_id

    if not student_id:
        raise HTTPException(
            status_code=400, detail="Assignment not assigned to specific student"
        )

    result = await db.execute(
        select(Chat).where(
            (Chat.teacher_id == teacher_id)
            & (Chat.student_id == student_id)
            & (Chat.assignment_id == assignment_id)
        )
    )
    chat = result.scalar_one_or_none()

    if not chat:
        chat = Chat(
            teacher_id=teacher_id, student_id=student_id, assignment_id=assignment_id
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)

    return {"chat_id": chat.id}


@router.delete("/{chat_id}/messages")
async def clear_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Очистить историю сообщений в чате"""

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")

    await db.execute(delete(Message).where(Message.chat_id == chat_id))
    await db.commit()

    await db.execute(
        update(Chat).where(Chat.id == chat_id).values(updated_at=func.now())
    )
    await db.commit()

    await sio.emit("chat_cleared", {"chat_id": chat_id}, room=f"chat_{chat_id}")

    return {"message": "Chat history cleared"}


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Полностью удалить чат"""

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(chat)
    await db.commit()

    await sio.emit("chat_deleted", {"chat_id": chat_id}, room=f"chat_{chat_id}")

    return {"message": "Chat deleted"}


@router.put("/messages/{message_id}")
async def edit_message(
    message_id: int,
    new_message: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Редактирование сообщения (только автор)"""

    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only edit your own messages"
        )

    message.message = new_message
    await db.commit()

    await sio.emit(
        "message_edited",
        {
            "message_id": message_id,
            "new_message": new_message,
            "chat_id": message.chat_id,
        },
        room=f"chat_{message.chat_id}",
    )

    return {"message": "Message updated"}


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление сообщения (автор или учитель ЭТОГО чата)"""

    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    chat_result = await db.execute(select(Chat).where(Chat.id == message.chat_id))
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    is_author = message.sender_id == current_user.id
    is_teacher_of_chat = (
        current_user.role == "teacher" and chat.teacher_id == current_user.id
    )

    if not (is_author or is_teacher_of_chat):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this message",
        )

    if message.files:
        try:
            files = json.loads(message.files)
            for file_url in files:
                delete_file(file_url)
        except Exception:
            pass

    await db.delete(message)
    await db.commit()

    await sio.emit(
        "message_deleted",
        {"message_id": message_id, "chat_id": message.chat_id},
        room=f"chat_{message.chat_id}",
    )

    return {"message": "Message deleted"}


@router.get("/{chat_id}/search")
async def search_messages(
    chat_id: int,
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Поиск сообщений в чате по тексту"""

    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in (chat.teacher_id, chat.student_id):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .where(Message.message.ilike(f"%{q}%"))
        .order_by(Message.created_at)
        .limit(50)
    )
    messages = result.scalars().all()

    return messages