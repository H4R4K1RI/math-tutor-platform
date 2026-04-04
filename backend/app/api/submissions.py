from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List

from app.db.database import get_db
from app.models.user import User
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.schemas.submission import (
    SubmissionCreate, SubmissionUpdate, 
    SubmissionResponse, SubmissionListResponse
)
from app.core.dependencies import get_current_user, get_current_teacher

router = APIRouter(prefix="/submissions", tags=["submissions"])

@router.post("/", response_model=SubmissionResponse)
async def create_submission(
    submission_data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отправка решения (только для учеников)"""
    
    # Проверяем, что пользователь не учитель
    if current_user.role == "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers cannot submit solutions"
        )
    
    # Проверяем, существует ли задание
    result = await db.execute(
        select(Assignment).where(Assignment.id == submission_data.assignment_id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Проверяем, имеет ли ученик доступ к заданию
    if assignment.student_id not in (None, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this assignment"
        )
    
    # Проверяем, не отправлял ли ученик уже решение на это задание
    result = await db.execute(
        select(Submission).where(
            (Submission.assignment_id == submission_data.assignment_id) &
            (Submission.student_id == current_user.id)
        )
    )
    existing_submission = result.scalar_one_or_none()
    
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a solution for this assignment"
        )
    
    # Создаём решение
    new_submission = Submission(
        content=submission_data.content,
        files=submission_data.files,
        assignment_id=submission_data.assignment_id,
        student_id=current_user.id,
        status="pending"
    )
    
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)
    
    return new_submission

@router.get("/", response_model=List[SubmissionListResponse])
async def get_submissions(
    assignment_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение списка решений"""
    
    if current_user.role == "teacher":
        # Учитель видит все решения
        if assignment_id:
            result = await db.execute(
                select(Submission).where(Submission.assignment_id == assignment_id)
                .order_by(Submission.submitted_at)
            )
        else:
            result = await db.execute(
                select(Submission).order_by(Submission.submitted_at)
            )
    else:
        # Ученик видит только свои решения
        if assignment_id:
            result = await db.execute(
                select(Submission).where(
                    (Submission.student_id == current_user.id) &
                    (Submission.assignment_id == assignment_id)
                ).order_by(Submission.submitted_at)
            )
        else:
            result = await db.execute(
                select(Submission).where(Submission.student_id == current_user.id)
                .order_by(Submission.submitted_at)
            )
    
    submissions = result.scalars().all()
    return submissions

@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение деталей решения"""
    
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Проверка прав доступа
    if current_user.role != "teacher" and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this submission"
        )
    
    return submission

@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: int,
    submission_data: SubmissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление решения (только для учителя - проверка)"""
    
    # Только учитель может менять статус и фидбек
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can review submissions"
        )
    
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Обновляем только переданные поля
    if submission_data.status is not None:
        submission.status = submission_data.status
    if submission_data.feedback is not None:
        submission.feedback = submission_data.feedback
    
    await db.commit()
    await db.refresh(submission)
    
    return submission

@router.delete("/{submission_id}")
async def delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление решения (только для учителя или автора)"""
    
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Проверка прав: учитель или автор решения
    if current_user.role != "teacher" and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this submission"
        )
    
    await db.delete(submission)
    await db.commit()
    
    return {"message": "Submission deleted successfully"}