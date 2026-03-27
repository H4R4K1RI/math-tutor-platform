from fastapi import FastAPI
from app.api import auth

app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.1.0",
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Math Tutor API is running", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}