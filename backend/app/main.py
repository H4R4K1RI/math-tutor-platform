from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api import auth, assignments, submissions, uploads, users
from app.socket_manager import socket_app, sio
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.7.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)

app.state.limiter = limiter

# Кастомный обработчик rate limit
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Слишком много попыток входа. Пожалуйста, подождите 1 минуту перед следующей попыткой."
        }
    )

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://90.156.170.9:5173",
        "http://localhost:5173",
        "http://tutor-platform.ru:5173",
        "http://www.tutor-platform.ru:5173",
        "https://tutor-platform.ru",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["90.156.170.9", "localhost", "127.0.0.1", "tutor-platform.ru", "www.tutor-platform.ru"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # CSP пока отключаем для простоты, но можно настроить позже
    # response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


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
