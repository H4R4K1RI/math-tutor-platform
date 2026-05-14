import socketio
from app.models.chat import Chat, Message
from app.db.database import AsyncSessionLocal
from sqlalchemy import select, update, func

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

socket_app = socketio.ASGIApp(sio)

connected_users = {}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    return True

@sio.event
async def disconnect(sid):
    if sid in connected_users:
        del connected_users[sid]
    print(f"Client disconnected: {sid}")

@sio.event
async def join_chat(sid, data):
    chat_id = data.get('chat_id')
    if chat_id:
        await sio.enter_room(sid, f"chat_{chat_id}")
        print(f"Client {sid} joined chat {chat_id}")

@sio.event
async def send_message(sid, data):
    sender_id = data.get('sender_id')
    chat_id = data.get('chat_id')
    message_text = data.get('message', '').strip()
    
    if not message_text or not sender_id or not chat_id:
        return
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Chat).where(Chat.id == chat_id))
        chat = result.scalar_one_or_none()
        
        if not chat:
            return
        
        if sender_id not in (chat.teacher_id, chat.student_id):
            return
        
        new_message = Message(
            chat_id=chat_id,
            sender_id=sender_id,
            message=message_text,
            is_read=False
        )
        db.add(new_message)
        await db.execute(update(Chat).where(Chat.id == chat_id).values(updated_at=func.now()))
        await db.commit()
        await db.refresh(new_message)
    
    room = f"chat_{chat_id}"
    await sio.emit('new_message', {
        'id': new_message.id,
        'chat_id': chat_id,
        'sender_id': sender_id,
        'message': message_text,
        'created_at': new_message.created_at.isoformat(),
        'is_read': False
    }, room=room)

@sio.event
async def mark_messages_read(sid, data):
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    
    if not chat_id or not user_id:
        return
    
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.sender_id != user_id)
            .where(Message.is_read == False)
            .values(is_read=True)
        )
        await db.commit()
    
    # Глобальная отправка, чтобы обновить счётчики у всех клиентов
    print(f"📤 Sending messages_read globally for chat {chat_id}")
    await sio.emit('messages_read', {'chat_id': chat_id, 'user_id': user_id})

@sio.event
async def typing_start(sid, data):
    chat_id = data.get('chat_id')
    if chat_id:
        await sio.emit('user_typing', {
            'chat_id': chat_id,
            'is_typing': True
        }, room=f"chat_{chat_id}", skip_sid=sid)

@sio.event
async def typing_stop(sid, data):
    chat_id = data.get('chat_id')
    if chat_id:
        await sio.emit('user_typing', {
            'chat_id': chat_id,
            'is_typing': False
        }, room=f"chat_{chat_id}", skip_sid=sid)