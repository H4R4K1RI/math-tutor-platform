from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any

from app.db.database import get_db
from app.models.user import User
from app.models.submission import Submission
from app.models.assignment import Assignment
from app.models.student_progress import StudentProgress
from app.core.dependencies import get_current_user, get_current_teacher

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/")
async def get_my_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить список учеников учителя с прогрессом"""
    
    # Находим всех студентов, у которых есть чаты/задания с этим учителем
    result = await db.execute(
        select(User)
        .join(Submission, Submission.student_id == User.id)
        .where(Submission.assignment_id.in_(
            select(Assignment.id).where(Assignment.teacher_id == current_user.id)
        ))
        .distinct()
    )
    students = result.scalars().all()
    
    students_data = []
    for student in students:
        # Общее количество заданий (личные + для всех)
        total_result = await db.execute(
            select(func.count(Assignment.id))
            .where(Assignment.teacher_id == current_user.id)
            .where(
                (Assignment.student_id == student.id) | (Assignment.student_id.is_(None))
            )
        )
        total_assignments = total_result.scalar() or 0
        
        # Количество выполненных (approved)
        completed_result = await db.execute(
            select(func.count(Submission.id))
            .where(Submission.student_id == student.id)
            .where(Submission.status == "approved")
            .where(
                Submission.assignment_id.in_(
                    select(Assignment.id).where(Assignment.teacher_id == current_user.id)
                )
            )
        )
        completed = completed_result.scalar() or 0
        
        progress_percent = min(int((completed / total_assignments * 100)) if total_assignments > 0 else 0, 100)
        
        students_data.append({
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "total_assignments": total_assignments,
            "completed": completed,
            "progress": progress_percent,
        })
    
    return students_data

@router.get("/{student_id}/stats")
async def get_student_stats(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить детальную статистику ученика"""
    
    # Проверяем доступ
    result = await db.execute(
        select(Assignment)
        .where(Assignment.teacher_id == current_user.id)
        .where(
            (Assignment.student_id == student_id) | (Assignment.student_id.is_(None))
        )
        .limit(1)
    )
    if not result.scalar_one_or_none():
        chat_result = await db.execute(
            select(Chat).where(
                Chat.teacher_id == current_user.id,
                Chat.student_id == student_id
            )
        )
        if not chat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this student"
            )
    
    # Получаем ученика
    result = await db.execute(select(User).where(User.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Получаем ВСЕ задания (личные + для всех)
    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.teacher_id == current_user.id)
        .where(
            (Assignment.student_id == student_id) | (Assignment.student_id.is_(None))
        )
        .order_by(Assignment.due_date)
    )
    assignments = assignments_result.scalars().all()
    
    # Получаем решения ученика по заданиям этого учителя
    submissions_result = await db.execute(
        select(Submission)
        .where(Submission.student_id == student_id)
        .where(
            Submission.assignment_id.in_(
                select(Assignment.id).where(Assignment.teacher_id == current_user.id)
            )
        )
    )
    submissions = {s.assignment_id: s for s in submissions_result.scalars().all()}
    
    # Формируем список заданий
    assignments_data = []
    for assignment in assignments:
        sub = submissions.get(assignment.id)
        assignments_data.append({
            "id": assignment.id,
            "title": assignment.title,
            "due_date": assignment.due_date,
            "status": sub.status if sub else "not_submitted",
            "feedback": sub.feedback if sub else None,
        })
    
    # Статистика (на основе ВСЕХ заданий)
    total = len(assignments)
    completed = sum(1 for a in assignments_data if a["status"] == "approved")
    pending = sum(1 for a in assignments_data if a["status"] == "pending")
    rejected = sum(1 for a in assignments_data if a["status"] == "rejected")
    progress = int((completed / total * 100)) if total > 0 else 0
    
    return {
        "student": {
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "registered_at": student.created_at
        },
        "stats": {
            "total_assignments": total,
            "completed": completed,
            "pending": pending,
            "rejected": rejected,
            "progress": progress
        },
        "assignments": assignments_data
    }