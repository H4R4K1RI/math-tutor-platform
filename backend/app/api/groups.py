from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List

from app.db.database import get_db
from app.models.user import User
from app.models.group import Group
from app.models.group_student import GroupStudent
from app.core.dependencies import get_current_teacher
from pydantic import BaseModel

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

@router.get("/")
async def get_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получить все группы учителя"""
    
    result = await db.execute(
        select(Group).where(Group.teacher_id == current_user.id)
    )
    groups = result.scalars().all()
    
    response = []
    for group in groups:
        # Подсчитываем количество учеников в группе
        count_result = await db.execute(
            select(GroupStudent).where(GroupStudent.group_id == group.id)
        )
        student_count = len(count_result.scalars().all())
        
        response.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "student_count": student_count,
            "created_at": group.created_at.isoformat()
        })
    
    return response


@router.post("/")
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создать новую группу"""
    
    new_group = Group(
        teacher_id=current_user.id,
        name=group_data.name,
        description=group_data.description
    )
    
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    
    return {
        "id": new_group.id,
        "name": new_group.name,
        "description": new_group.description,
        "created_at": new_group.created_at.isoformat()
    }


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
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
    current_user: User = Depends(get_current_teacher)
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
    current_user: User = Depends(get_current_teacher)
):
    """Добавить ученика в группу"""
    
    # Проверяем, что группа принадлежит учителю
    group_result = await db.execute(
        select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Проверяем, что ученик не уже в группе
    existing = await db.execute(
        select(GroupStudent).where(
            GroupStudent.group_id == group_id,
            GroupStudent.student_id == student_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Student already in group")
    
    group_student = GroupStudent(
        group_id=group_id,
        student_id=student_id
    )
    
    db.add(group_student)
    await db.commit()
    
    return {"message": "Student added to group"}


@router.delete("/{group_id}/students/{student_id}")
async def remove_student_from_group(
    group_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удалить ученика из группы"""
    
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
    current_user: User = Depends(get_current_teacher)
):
    """Получить учеников группы"""
    
    # Проверяем группу
    group_result = await db.execute(
        select(Group).where(Group.id == group_id, Group.teacher_id == current_user.id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Получаем учеников
    result = await db.execute(
        select(User)
        .join(GroupStudent, GroupStudent.student_id == User.id)
        .where(GroupStudent.group_id == group_id)
    )
    students = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "name": s.full_name,
            "email": s.email
        }
        for s in students
    ]