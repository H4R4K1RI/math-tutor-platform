from fastapi import FastAPI
from app.api import auth

app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.2.0"
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/api", tags=["authentication"])

@app.get("/")
async def root():
    return {"message": "Math Tutor API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}