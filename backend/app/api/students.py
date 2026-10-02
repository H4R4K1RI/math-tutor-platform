from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_teacher
from app.shared.db import get_db
from app.models.assignment import Assignment
from app.models.chat import Chat
from app.models.group import Group
from app.models.group_student import GroupStudent
from app.models.lesson import Lesson
from app.models.submission import Submission
from app.models.user import User

router = APIRouter(prefix="/students", tags=["students"])


async def get_teacher_student_ids(db: AsyncSession, teacher_id: int) -> set[int]:
    """Собрать ID всех УЧЕНИКОВ, связанных с учителем любым способом."""

    student_ids: set[int] = set()

    result = await db.execute(
        select(Assignment.student_id)
        .where(Assignment.teacher_id == teacher_id)
        .where(Assignment.student_id.isnot(None))
        .distinct()
    )
    student_ids.update(row[0] for row in result.all() if row[0])

    result = await db.execute(
        select(Chat.student_id).where(Chat.teacher_id == teacher_id).distinct()
    )
    student_ids.update(row[0] for row in result.all() if row[0])

    result = await db.execute(
        select(Lesson.student_id).where(Lesson.teacher_id == teacher_id).distinct()
    )
    student_ids.update(row[0] for row in result.all() if row[0])

    result = await db.execute(
        select(GroupStudent.student_id)
        .join(Group, GroupStudent.group_id == Group.id)
        .where(Group.teacher_id == teacher_id)
        .distinct()
    )
    student_ids.update(row[0] for row in result.all() if row[0])

    if not student_ids:
        return set()

    result = await db.execute(
        select(User.id)
        .where(User.id.in_(student_ids))
        .where(User.role == "student")
        .where(User.is_active.is_(True))
    )
    valid_ids = {row[0] for row in result.all()}

    return valid_ids


@router.get("/")
async def get_my_students(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить список учеников учителя (оптимизировано)"""

    student_ids = await get_teacher_student_ids(db, current_user.id)

    if not student_ids:
        return {"items": [], "total": 0, "skip": skip, "limit": limit}

    total = len(student_ids)

    sorted_ids = sorted(student_ids)
    page_ids = sorted_ids[skip : skip + limit]

    if not page_ids:
        return {"items": [], "total": total, "skip": skip, "limit": limit}

    # Ученики
    result = await db.execute(select(User).where(User.id.in_(page_ids)))
    students = result.scalars().all()
    student_ids_set = [s.id for s in students]

    # 1. Общее количество заданий для каждого ученика (личные + общие)
    assignments_count_result = await db.execute(
        select(
            Assignment.student_id,
            func.count(Assignment.id),
        )
        .where(Assignment.teacher_id == current_user.id)
        .where(Assignment.student_id.in_(student_ids_set))
        .group_by(Assignment.student_id)
    )
    assignments_counts = {row[0]: row[1] for row in assignments_count_result.all()}

    # 2. Общие задания (student_id IS NULL)
    common_count_result = await db.execute(
        select(func.count(Assignment.id))
        .where(Assignment.teacher_id == current_user.id)
        .where(Assignment.student_id.is_(None))
    )
    common_count = common_count_result.scalar() or 0

    # 3. Выполненные (approved) по каждому ученику
    completed_result = await db.execute(
        select(
            Submission.student_id,
            func.count(Submission.id),
        )
        .where(Submission.student_id.in_(student_ids_set))
        .where(Submission.status == "approved")
        .where(
            Submission.assignment_id.in_(
                select(Assignment.id).where(Assignment.teacher_id == current_user.id)
            )
        )
        .group_by(Submission.student_id)
    )
    completed_counts = {row[0]: row[1] for row in completed_result.all()}

    students_data = []
    for student in students:
        total_assignments = (
            assignments_counts.get(student.id, 0) + common_count
        )
        completed = completed_counts.get(student.id, 0)

        progress_percent = min(
            int((completed / total_assignments * 100))
            if total_assignments > 0
            else 0,
            100,
        )

        students_data.append(
            {
                "id": student.id,
                "name": student.full_name,
                "email": student.email,
                "total_assignments": total_assignments,
                "completed": completed,
                "progress": progress_percent,
            }
        )

    return {
        "items": students_data,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{student_id}/stats")
async def get_student_stats(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить детальную статистику ученика (оптимизировано)"""

    student_ids = await get_teacher_student_ids(db, current_user.id)
    if student_id not in student_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this student",
        )

    result = await db.execute(select(User).where(User.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.teacher_id == current_user.id)
        .where(
            (Assignment.student_id == student_id) | (Assignment.student_id.is_(None))
        )
        .order_by(Assignment.due_date)
    )
    assignments = assignments_result.scalars().all()

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

    assignments_data = []
    for assignment in assignments:
        sub = submissions.get(assignment.id)
        assignments_data.append(
            {
                "id": assignment.id,
                "title": assignment.title,
                "due_date": assignment.due_date,
                "status": sub.status if sub else "not_submitted",
                "feedback": sub.feedback if sub else None,
            }
        )

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
            "registered_at": student.created_at,
        },
        "stats": {
            "total_assignments": total,
            "completed": completed,
            "pending": pending,
            "rejected": rejected,
            "progress": progress,
        },
        "assignments": assignments_data,
    }