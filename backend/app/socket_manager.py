import socketio
from sqlalchemy import func, select, update
from jose import JWTError, jwt

from app.shared.config import settings
from app.shared.logger import logger
from app.shared.db import AsyncSessionLocal
from app.models.chat import Chat, Message
from app.auth.models import User

# CORS нужен для Socket.IO, без дублирования с FastAPI
sio = socketio.AsyncServer(
    cors_allowed_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "https://tutor-platform.ru",
        "https://www.tutor-platform.ru",
    ],
    async_mode="asgi",
)

socket_app = socketio.ASGIApp(sio)

# sid -> user_id (доверенный, из JWT)
connected_users: dict[str, int] = {}


def _extract_token_from_cookie(environ: dict) -> str | None:
    """Извлекаем access_token из Cookie-заголовка."""
    cookie_header = environ.get("HTTP_COOKIE", "")
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("access_token="):
            return part[len("access_token="):]
    return None


def _decode_user_id(token: str) -> int | None:
    """Декодируем JWT и достаём user_id. None — если невалидный."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        user_id = payload.get("user_id")
        return int(user_id) if user_id else None
    except (JWTError, ValueError, TypeError):
        return None


@sio.event
async def connect(sid, environ):
    """Аутентификация при подключении через JWT в cookie."""
    token = _extract_token_from_cookie(environ)
    if not token:
        logger.warning(f"Socket connect rejected (no token): {sid}")
        raise socketio.exceptions.ConnectionRefusedError("Not authenticated")

    user_id = _decode_user_id(token)
    if not user_id:
        logger.warning(f"Socket connect rejected (invalid token): {sid}")
        raise socketio.exceptions.ConnectionRefusedError("Invalid token")

    # Проверяем, что пользователь существует и активен
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            logger.warning(f"Socket connect rejected (user not found/inactive): {sid}")
            raise socketio.exceptions.ConnectionRefusedError("User not found or inactive")

    connected_users[sid] = user_id
    logger.info(f"Client connected: {sid} (user_id={user_id})")

    # Подписываем на все чаты пользователя
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Chat).where(
                (Chat.teacher_id == user_id) | (Chat.student_id == user_id)
            )
        )
        chats = result.scalars().all()

    for chat in chats:
        await sio.enter_room(sid, f"chat_{chat.id}")

    logger.info(f"User {user_id} joined {len(chats)} chats")
    return True


@sio.event
async def disconnect(sid):
    connected_users.pop(sid, None)
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def join_chat(sid, data):
    """Присоединиться к комнате чата (только если пользователь — участник)."""
    user_id = connected_users.get(sid)
    if not user_id:
        return

    chat_id = data.get("chat_id")
    if not chat_id:
        return

    # Проверяем, что пользователь — участник чата
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Chat).where(Chat.id == chat_id))
        chat = result.scalar_one_or_none()

    if not chat or user_id not in (chat.teacher_id, chat.student_id):
        logger.warning(f"User {user_id} tried to join chat {chat_id} without access")
        return

    await sio.enter_room(sid, f"chat_{chat_id}")
    logger.info(f"Client {sid} joined chat {chat_id}")


@sio.event
async def send_message(sid, data):
    """Отправить сообщение. sender_id берётся из сессии, а не из data."""
    user_id = connected_users.get(sid)
    if not user_id:
        return

    chat_id = data.get("chat_id")
    message_text = (data.get("message") or "").strip()

    if not chat_id or not message_text:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Chat).where(Chat.id == chat_id))
        chat = result.scalar_one_or_none()

        if not chat:
            return

        # Проверяем, что sender_id — участник
        if user_id not in (chat.teacher_id, chat.student_id):
            logger.warning(f"User {user_id} tried to send to chat {chat_id} without access")
            return

        new_message = Message(
            chat_id=chat_id,
            sender_id=user_id,
            message=message_text,
            is_read=False,
        )
        db.add(new_message)
        await db.execute(
            update(Chat).where(Chat.id == chat_id).values(updated_at=func.now())
        )
        await db.commit()
        await db.refresh(new_message)

    room = f"chat_{chat_id}"
    await sio.emit(
        "new_message",
        {
            "id": new_message.id,
            "chat_id": chat_id,
            "sender_id": user_id,
            "message": message_text,
            "created_at": new_message.created_at.isoformat(),
            "is_read": False,
        },
        room=room,
    )


@sio.event
async def mark_messages_read(sid, data):
    """Пометить сообщения прочитанными. user_id берётся из сессии."""
    user_id = connected_users.get(sid)
    if not user_id:
        return

    chat_id = data.get("chat_id")
    if not chat_id:
        return

    # Проверяем, что пользователь — участник
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Chat).where(Chat.id == chat_id))
        chat = result.scalar_one_or_none()
        if not chat or user_id not in (chat.teacher_id, chat.student_id):
            return

        await db.execute(
            update(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.sender_id != user_id)
            .where(Message.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        await db.commit()

    # Эмитим ТОЛЬКО в комнату чата, а не всем
    await sio.emit(
        "messages_read",
        {"chat_id": chat_id, "user_id": user_id},
        room=f"chat_{chat_id}",
    )


@sio.event
async def typing_start(sid, data):
    user_id = connected_users.get(sid)
    if not user_id:
        return
    chat_id = data.get("chat_id")
    if chat_id:
        await sio.emit(
            "user_typing",
            {"chat_id": chat_id, "user_id": user_id, "is_typing": True},
            room=f"chat_{chat_id}",
            skip_sid=sid,
        )


@sio.event
async def typing_stop(sid, data):
    user_id = connected_users.get(sid)
    if not user_id:
        return
    chat_id = data.get("chat_id")
    if chat_id:
        await sio.emit(
            "user_typing",
            {"chat_id": chat_id, "user_id": user_id, "is_typing": False},
            room=f"chat_{chat_id}",
            skip_sid=sid,
        )