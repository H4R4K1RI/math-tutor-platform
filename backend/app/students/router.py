from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher
from app.auth.models import User
from app.shared.db import get_db
from app.students.service import StudentsService

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/")
async def get_my_students(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Список учеников учителя (оптимизировано)."""
    service = StudentsService(db)
    return await service.get_my_students(current_user.id, skip, limit)


@router.get("/{student_id}/stats")
async def get_student_stats(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Детальная статистика ученика."""
    service = StudentsService(db)
    return await service.get_student_stats(student_id, current_user.id)