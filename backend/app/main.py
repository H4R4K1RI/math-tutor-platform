import asyncio
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import uploads
from app.assignments.router import router as assignments_router
from app.auth.router import router as auth_router
from app.board.router import router as board_router
from app.chat.router import router as chat_router
from app.chat.socket import socket_app
from app.groups.router import router as groups_router
from app.invitations.router import router as invitations_router
from app.lessons.router import router as lessons_router
from app.materials.router import router as materials_router
from app.notifications.reminder_scheduler import run_scheduler
from app.payments.router import router as payments_router
from app.reviews.router import router as reviews_router
from app.shared.logger import logger
from app.students.router import router as students_router
from app.tests.router import router as tests_router
from app.tutoring_requests.router import router as tutoring_requests_router
from app.users.router import router as users_router
from app.video.router import router as video_router


# ==================== RATE LIMITER ====================

if os.getenv("TESTING") == "1":
    limiter = Limiter(key_func=get_remote_address, enabled=False)
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


# ==================== APP ====================

app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.7.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

# Глобальный флаг для задачи планировщика
scheduler_task = None


@app.on_event("startup")
async def startup():
    global scheduler_task
    logger.info("Application startup complete")

    scheduler_task = asyncio.create_task(run_scheduler())
    logger.info("Reminder scheduler task created")


@app.on_event("shutdown")
async def shutdown():
    global scheduler_task
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        logger.info("Reminder scheduler task cancelled")


app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Слишком много попыток входа. Пожалуйста, подождите 1 минуту перед следующей попыткой."
        },
    )


# ==================== MIDDLEWARE ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://tutor-platform.localhost",
        "https://tutor-platform.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# ==================== STATIC ====================

static_dir = "uploads"
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ==================== ROUTERS ====================

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(invitations_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(groups_router, prefix="/api")
app.include_router(assignments_router, prefix="/api")
app.include_router(board_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(tests_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(materials_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(tutoring_requests_router, prefix="/api")
app.include_router(video_router, prefix="/api")
app.include_router(uploads.router, prefix="/api", tags=["upload"])


# ==================== HEALTH ====================

@app.get("/")
async def root():
    return {"message": "Math Tutor API is running", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ==================== SOCKET.IO ====================

app.mount("/socket.io/", socket_app)