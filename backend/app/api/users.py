from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_teacher

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/students", response_model=list[UserResponse])
async def get_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить список всех учеников (только для учителя)"""
    result = await db.execute(
        select(User).where(User.role == "student")
    )
    students = result.scalars().all()
    return students