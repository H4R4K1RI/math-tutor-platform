from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_teacher
from app.shared.db import get_db
from app.models.group import Group
from app.models.group_student import GroupStudent
from app.models.user import User

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    student_count: int
    created_at: str


async def _get_teacher_student_ids(db: AsyncSession, teacher_id: int) -> set[int]:
    """ID учеников, связанных с учителем (через чаты)."""
    from app.models.chat import Chat

    result = await db.execute(
        select(Chat.student_id).where(Chat.teacher_id == teacher_id).distinct()
    )
    return {row[0] for row in result.all() if row[0]}


@router.get("/")
async def get_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить все группы учителя (оптимизировано)"""

    result = await db.execute(select(Group).where(Group.teacher_id == current_user.id))
    groups = result.scalars().all()

    if not groups:
        return []

    group_ids = [g.id for g in groups]

    count_result = await db.execute(
        select(GroupStudent.group_id, func.count(GroupStudent.id))
        .where(GroupStudent.group_id.in_(group_ids))
        .group_by(GroupStudent.group_id)
    )
    counts = {row[0]: row[1] for row in count_result.all()}

    response = []
    for group in groups:
        response.append(
            {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "student_count": counts.get(group.id, 0),
                "created_at": group.created_at.isoformat(),
            }
        )

    return response


@router.post("/")
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создать новую группу"""

    new_group = Group(
        teacher_id=current_user.id,
        name=group_data.name,
        description=group_data.description,
    )

    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)

    return {
        "id": new_group.id,
        "name": new_group.name,
        "description": new_group.description,
        "created_at": new_group.created_at.isoformat(),
    }


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить группу"""

    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group_data.name is not None:
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description

    await db.commit()

    return {"message": "Group updated"}


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить группу"""

    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await db.delete(group)
    await db.commit()

    return {"message": "Group deleted"}


@router.post("/{group_id}/students/{student_id}")
async def add_student_to_group(
    group_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Добавить ученика в группу"""

    group_result = await db.execute(
        select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    teacher_student_ids = await _get_teacher_student_ids(db, current_user.id)
    if student_id not in teacher_student_ids:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this student",
        )

    existing = await db.execute(
        select(GroupStudent).where(
            GroupStudent.group_id == group_id, GroupStudent.student_id == student_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Student already in group")

    group_student = GroupStudent(group_id=group_id, student_id=student_id)

    db.add(group_student)
    await db.commit()

    return {"message": "Student added to group"}


@router.delete("/{group_id}/students/{student_id}")
async def remove_student_from_group(
    group_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить ученика из группы"""

    group_result = await db.execute(
        select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    result = await db.execute(
        delete(GroupStudent)
        .where(GroupStudent.group_id == group_id)
        .where(GroupStudent.student_id == student_id)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not in group")

    await db.commit()

    return {"message": "Student removed from group"}


@router.get("/{group_id}/students")
async def get_group_students(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить учеников группы"""

    group_result = await db.execute(
        select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    result = await db.execute(
        select(User)
        .join(GroupStudent, GroupStudent.student_id == User.id)
        .where(GroupStudent.group_id == group_id)
    )
    students = result.scalars().all()

    return [{"id": s.id, "name": s.full_name, "email": s.email} for s in students]