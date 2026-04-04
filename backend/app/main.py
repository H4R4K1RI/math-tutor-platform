from fastapi import FastAPI
from app.api import auth, assignments  # Добавили assignments

app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.3.0"
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(assignments.router, prefix="/api", tags=["assignments"])

@app.get("/")
async def root():
    return {"message": "Math Tutor API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}