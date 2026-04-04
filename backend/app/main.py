from fastapi import FastAPI
from app.api import auth, assignments, submissions, uploads
from fastapi.staticfiles import StaticFiles
import os


app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.4.0",
    swagger_ui_parameters={
        "persistAuthorization": True,  
    }
)

static_dir = "uploads"
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(assignments.router, prefix="/api", tags=["assignments"])
app.include_router(submissions.router, prefix="/api", tags=["submissions"])
app.include_router(uploads.router, prefix="/api", tags=["upload"])



@app.get("/")
async def root():
    return {"message": "Math Tutor API is running", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}