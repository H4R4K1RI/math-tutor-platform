from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api import auth, assignments, submissions, uploads, users
from app.socket_manager import socket_app, sio

app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.6.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://90.156.170.9:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика
static_dir = "uploads"
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Роутеры API
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(assignments.router, prefix="/api", tags=["assignments"])
app.include_router(submissions.router, prefix="/api", tags=["submissions"])
app.include_router(uploads.router, prefix="/api", tags=["upload"])
app.include_router(users.router, prefix="/api", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Math Tutor API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Монтируем Socket.IO на /socket.io/
app.mount("/socket.io/", socket_app)

# Socket.IO события
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
