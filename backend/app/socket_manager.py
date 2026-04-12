import socketio

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
