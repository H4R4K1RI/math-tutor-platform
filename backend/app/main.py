from fastapi import FastAPI
from app.api import auth, assignments, submissions

app = FastAPI(
    title="Math Tutor Platform",
    description="Платформа для репетитора по математике",
    version="0.4.0",
    swagger_ui_parameters={
        "persistAuthorization": True,  
    }
)

app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(assignments.router, prefix="/api", tags=["assignments"])
app.include_router(submissions.router, prefix="/api", tags=["submissions"])


@app.get("/")
async def root():
    return {"message": "Math Tutor API is running", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}