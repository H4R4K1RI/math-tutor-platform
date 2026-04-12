from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from typing import List, Optional

from app.socket_manager import sio
from app.db.database import get_db
from app.models.user import User
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, 
    AssignmentResponse, AssignmentListResponse
)
from app.core.dependencies import get_current_user, get_current_teacher

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)  # Только учитель
):
    """Создание нового задания (только для учителя)"""
    
    new_assignment = Assignment(
        title=assignment_data.title,
        description=assignment_data.description,
        attachments=assignment_data.attachments,
        due_date=assignment_data.due_date,
        teacher_id=current_user.id,
        student_id=assignment_data.student_id
    )
    
    db.add(new_assignment)
    await db.commit()
    await sio.emit('assignment_updated', {'action': 'created', 'assignment_id': new_assignment.id})
    await db.refresh(new_assignment)


    
    return new_assignment

@router.get("/")
async def get_assignments(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "teacher":
        query = select(Assignment).order_by(Assignment.due_date)
        total_query = select(func.count()).select_from(Assignment)
    else:
        query = select(Assignment).where(
            (Assignment.student_id == current_user.id) |
            (Assignment.student_id.is_(None))
        ).order_by(Assignment.due_date)
        total_query = select(func.count()).where(
            (Assignment.student_id == current_user.id) |
            (Assignment.student_id.is_(None))
        ).select_from(Assignment)

    result = await db.execute(query.offset(skip).limit(limit))
    total_result = await db.execute(total_query)

    assignments = result.scalars().all()
    total = total_result.scalar()

    return {
        "items": assignments,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение деталей конкретного задания"""
    
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Проверка прав доступа
    if current_user.role != "teacher":
        if assignment.student_id not in (None, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this assignment"
            )
    
    return assignment

@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление задания (только для учителя)"""
    
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Обновляем только переданные поля
    update_data = assignment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    # Сбрасываем статус всех решений этого задания
    submissions_result = await db.execute(
        select(Submission).where(Submission.assignment_id == assignment_id)
    )
    submissions = submissions_result.scalars().all()
    
    for sub in submissions:
        sub.status = "pending"
        sub.feedback = None
    
    if submissions:
        await db.flush()
    
    await db.commit()
    await sio.emit('assignment_updated', {'action': 'updated','assignment_id': assignment_id})
    await db.refresh(assignment)
    
    return assignment

@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)  # Только учитель
):
    """Удаление задания (только для учителя)"""
    
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    await db.delete(assignment)
    await db.commit()
    await sio.emit('assignment_deleted', {
    'action': 'deleted',
    'assignment_id': assignment_id
})
    return {"message": "Assignment deleted successfully"}
