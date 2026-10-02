from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_teacher, get_current_user
from app.shared.db import get_db
from app.models.assignment import Assignment
from app.models.chat import Chat
from app.models.group_student import GroupStudent
from app.models.submission import Submission
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.socket_manager import sio

router = APIRouter(prefix="/assignments", tags=["assignments"])


async def _get_student_teacher_ids(db: AsyncSession, student_id: int) -> set[int]:
    """ID всех учителей, с которыми связан ученик (через чаты)."""
    result = await db.execute(
        select(Chat.teacher_id).where(Chat.student_id == student_id).distinct()
    )
    return {row[0] for row in result.all() if row[0]}


@router.post("/")
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создание нового задания (только для учителя).

    Если указан group_id — создаётся по одному заданию на каждого ученика группы.
    Возвращает {assignments: [...], count: N}.
    """

    if assignment_data.group_id:
        from app.models.group import Group

        group_result = await db.execute(
            select(Group).where(
                Group.id == assignment_data.group_id,
                Group.teacher_id == current_user.id,
            )
        )
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this group",
            )

        result = await db.execute(
            select(GroupStudent.student_id).where(
                GroupStudent.group_id == assignment_data.group_id
            )
        )
        students_ids = [row[0] for row in result.all()]

        if not students_ids:
            raise HTTPException(
                status_code=400,
                detail="Group has no students",
            )

        created_assignments = []
        for student_id in students_ids:
            new_assignment = Assignment(
                title=assignment_data.title,
                description=assignment_data.description,
                attachments=assignment_data.attachments,
                due_date=assignment_data.due_date,
                teacher_id=current_user.id,
                student_id=student_id,
                group_id=assignment_data.group_id,
            )
            db.add(new_assignment)
            created_assignments.append(new_assignment)

        await db.commit()
        for a in created_assignments:
            await db.refresh(a)

        await sio.emit(
            "assignment_updated",
            {
                "action": "created",
                "assignment_ids": [a.id for a in created_assignments],
                "count": len(created_assignments),
            },
        )

        return {
            "assignments": [
                {
                    "id": a.id,
                    "title": a.title,
                    "description": a.description,
                    "attachments": a.attachments,
                    "due_date": a.due_date.isoformat() if a.due_date else None,
                    "teacher_id": a.teacher_id,
                    "student_id": a.student_id,
                    "group_id": a.group_id,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in created_assignments
            ],
            "count": len(created_assignments),
        }

    # Одиночное задание
    new_assignment = Assignment(
        title=assignment_data.title,
        description=assignment_data.description,
        attachments=assignment_data.attachments,
        due_date=assignment_data.due_date,
        teacher_id=current_user.id,
        student_id=assignment_data.student_id,
        group_id=None,
    )

    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)

    await sio.emit(
        "assignment_updated",
        {"action": "created", "assignment_id": new_assignment.id},
    )

    return {
        "assignments": [
            {
                "id": new_assignment.id,
                "title": new_assignment.title,
                "description": new_assignment.description,
                "attachments": new_assignment.attachments,
                "due_date": new_assignment.due_date.isoformat() if new_assignment.due_date else None,
                "teacher_id": new_assignment.teacher_id,
                "student_id": new_assignment.student_id,
                "group_id": new_assignment.group_id,
                "created_at": new_assignment.created_at.isoformat() if new_assignment.created_at else None,
            }
        ],
        "count": 1,
    }


@router.get("/")
async def get_assignments(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить задания (учитель — только свои, ученик — только свои + от своих учителей)"""

    if current_user.role == "teacher":
        query = (
            select(Assignment)
            .where(Assignment.teacher_id == current_user.id)
            .order_by(Assignment.due_date)
        )
        total_query = (
            select(func.count())
            .where(Assignment.teacher_id == current_user.id)
            .select_from(Assignment)
        )
    else:
        teacher_ids = await _get_student_teacher_ids(db, current_user.id)

        if not teacher_ids:
            query = (
                select(Assignment)
                .where(Assignment.student_id == current_user.id)
                .order_by(Assignment.due_date)
            )
            total_query = (
                select(func.count())
                .where(Assignment.student_id == current_user.id)
                .select_from(Assignment)
            )
        else:
            query = (
                select(Assignment)
                .where(
                    (Assignment.student_id == current_user.id)
                    | (
                        (Assignment.student_id.is_(None))
                        & (Assignment.teacher_id.in_(teacher_ids))
                    )
                )
                .order_by(Assignment.due_date)
            )
            total_query = (
                select(func.count())
                .where(
                    (Assignment.student_id == current_user.id)
                    | (
                        (Assignment.student_id.is_(None))
                        & (Assignment.teacher_id.in_(teacher_ids))
                    )
                )
                .select_from(Assignment)
            )

    result = await db.execute(query.offset(skip).limit(limit))
    total_result = await db.execute(total_query)

    assignments = result.scalars().all()
    total = total_result.scalar()

    return {"items": assignments, "total": total, "skip": skip, "limit": limit}


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение деталей конкретного задания"""

    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    if current_user.role == "teacher":
        if assignment.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this assignment",
            )
    else:
        if assignment.student_id == current_user.id:
            pass
        elif assignment.student_id is None:
            teacher_ids = await _get_student_teacher_ids(db, current_user.id)
            if assignment.teacher_id not in teacher_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this assignment",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this assignment",
            )

    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновление задания (только для учителя)"""

    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    update_data = assignment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    submissions_result = await db.execute(
        select(Submission).where(Submission.assignment_id == assignment_id)
    )
    submissions = submissions_result.scalars().all()

    for sub in submissions:
        sub.status = "pending"
        sub.feedback = None

    await db.commit()

    await sio.emit(
        "assignment_updated", {"action": "updated", "assignment_id": assignment_id}
    )
    await db.refresh(assignment)

    return assignment


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удаление задания (только для учителя)"""

    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    await db.delete(assignment)
    await db.commit()

    await sio.emit(
        "assignment_deleted", {"action": "deleted", "assignment_id": assignment_id}
    )

    return {"message": "Assignment deleted successfully"}