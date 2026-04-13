import socketio
from app.models.chat import Chat, Message
from app.db.database import AsyncSessionLocal
from sqlalchemy import select, update, func

# Создаём сервер Socket.IO
sio = socketio.AsyncServer(
    cors_allowed_origins=[
        "http://90.156.170.9:5173",
        "http://localhost:5173",
        "http://tutor-platform.ru:5173",
        "http://www.tutor-platform.ru:5173",
        "https://tutor-platform.ru",
        "https://www.tutor-platform.ru",
    ],
    async_mode='asgi'
)

# Создаём ASGI приложение для Socket.IO
socket_app = socketio.ASGIApp(sio)

@sio.event
async def join_chat(sid, data):
    """Подключение к комнате чата"""
    chat_id = data.get('chat_id')
    if chat_id:
        sio.enter_room(sid, f"chat_{chat_id}")
        print(f"Client {sid} joined chat room {chat_id}")

@sio.event
async def send_message(sid, data):
    """Отправка сообщения в чат"""
    from sqlalchemy import select
    from app.models.user import User
    
    chat_id = data.get('chat_id')
    message_text = data.get('message', '').strip()
    sender_id = data.get('sender_id')
    
    if not message_text:
        return
    
    async with AsyncSessionLocal() as db:
        # Сохраняем сообщение в БД
        new_message = Message(
            chat_id=chat_id,
            sender_id=sender_id,
            message=message_text,
            is_read=False
        )
        db.add(new_message)
        
        # Обновляем updated_at в чате
        await db.execute(
            update(Chat).where(Chat.id == chat_id).values(updated_at=func.now())
        )
        
        await db.commit()
        await db.refresh(new_message)
        
        # Получаем информацию об отправителе
        result = await db.execute(
            select(User.id, User.full_name).where(User.id == sender_id)
        )
        sender = result.first()
    
    # Отправляем сообщение всем в комнате
    await sio.emit('new_message', {
        'id': new_message.id,
        'chat_id': chat_id,
        'sender_id': sender_id,
        'sender_name': sender.full_name if sender else 'Пользователь',
        'message': message_text,
        'created_at': new_message.created_at.isoformat(),
        'is_read': False
    }, room=f"chat_{chat_id}")

@sio.event
async def mark_messages_read(sid, data):
    """Отметить сообщения как прочитанные"""
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.sender_id != user_id)
            .where(Message.is_read == False)
            .values(is_read=True)
        )
        await db.commit()
    
    await sio.emit('messages_read', {'chat_id': chat_id, 'user_id': user_id}, room=f"chat_{chat_id}")