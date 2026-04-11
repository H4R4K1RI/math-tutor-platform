import socketio

sio = socketio.AsyncServer(
    cors_allowed_origins=[
        "http://90.156.170.9:5173",
        "http://localhost:5173"
    ],
    async_mode='asgi'

)
