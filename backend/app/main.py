from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api import auth, assignments, submissions, uploads, users

app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.5.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)

# Настройка CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка статической раздачи файлов
static_dir = "uploads"
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Подключаем роутеры
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