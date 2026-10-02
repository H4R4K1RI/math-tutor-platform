from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher
from app.auth.models import User
from app.groups.schemas import GroupCreate, GroupUpdate
from app.groups.service import GroupsService
from app.shared.db import get_db

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/")
async def get_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = GroupsService(db)
    return await service.get_groups(current_user.id)


@router.post("/")
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = GroupsService(db)
    return await service.create_group(current_user.id, group_data)


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = GroupsService(db)
    return await service.update_group(group_id, current_user.id, group_data)


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = GroupsService(db)
    return await service.delete_group(group_id, current_user.id)


@router.post("/{group_id}/students/{student_id}")
async def add_student_to_group(
    group_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = GroupsService(db)
    return await service.add_student_to_group(
        group_id, student_id, current_user.id
    )


@router.delete("/{group_id}/students/{student_id}")
async def remove_student_from_group(
    group_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = GroupsService(db)
    return await service.remove_student_from_group(
        group_id, student_id, current_user.id
    )


@router.get("/{group_id}/students")
async def get_group_students(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = GroupsService(db)
    return await service.get_group_students(group_id, current_user.id)