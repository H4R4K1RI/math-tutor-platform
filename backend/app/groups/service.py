from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.groups.schemas import GroupCreate, GroupUpdate
from app.groups.models import Group, GroupStudent
from app.students.service import get_teacher_student_ids


class GroupsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_groups(self, teacher_id: int) -> list[dict]:
        result = await self.db.execute(
            select(Group).where(Group.teacher_id == teacher_id)
        )
        groups = result.scalars().all()

        if not groups:
            return []

        group_ids = [g.id for g in groups]

        count_result = await self.db.execute(
            select(GroupStudent.group_id, func.count(GroupStudent.id))
            .where(GroupStudent.group_id.in_(group_ids))
            .group_by(GroupStudent.group_id)
        )
        counts = {row[0]: row[1] for row in count_result.all()}

        return [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "student_count": counts.get(g.id, 0),
                "created_at": g.created_at.isoformat(),
            }
            for g in groups
        ]

    async def create_group(self, teacher_id: int, data: GroupCreate) -> dict:
        new_group = Group(
            teacher_id=teacher_id,
            name=data.name,
            description=data.description,
        )
        self.db.add(new_group)
        await self.db.commit()
        await self.db.refresh(new_group)

        return {
            "id": new_group.id,
            "name": new_group.name,
            "description": new_group.description,
            "created_at": new_group.created_at.isoformat(),
        }

    async def update_group(
        self, group_id: int, teacher_id: int, data: GroupUpdate
    ) -> dict:
        result = await self.db.execute(
            select(Group).where(
                Group.id == group_id, Group.teacher_id == teacher_id
            )
        )
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        if data.name is not None:
            group.name = data.name
        if data.description is not None:
            group.description = data.description

        await self.db.commit()
        return {"message": "Group updated"}

    async def delete_group(self, group_id: int, teacher_id: int) -> dict:
        result = await self.db.execute(
            select(Group).where(
                Group.id == group_id, Group.teacher_id == teacher_id
            )
        )
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        await self.db.delete(group)
        await self.db.commit()
        return {"message": "Group deleted"}

    async def add_student_to_group(
        self, group_id: int, student_id: int, teacher_id: int
    ) -> dict:
        group_result = await self.db.execute(
            select(Group).where(
                Group.id == group_id, Group.teacher_id == teacher_id
            )
        )
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        teacher_student_ids = await get_teacher_student_ids(self.db, teacher_id)
        if student_id not in teacher_student_ids:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this student",
            )

        existing = await self.db.execute(
            select(GroupStudent).where(
                GroupStudent.group_id == group_id,
                GroupStudent.student_id == student_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Student already in group")

        self.db.add(GroupStudent(group_id=group_id, student_id=student_id))
        await self.db.commit()
        return {"message": "Student added to group"}

    async def remove_student_from_group(
        self, group_id: int, student_id: int, teacher_id: int
    ) -> dict:
        group_result = await self.db.execute(
            select(Group).where(
                Group.id == group_id, Group.teacher_id == teacher_id
            )
        )
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        result = await self.db.execute(
            delete(GroupStudent)
            .where(GroupStudent.group_id == group_id)
            .where(GroupStudent.student_id == student_id)
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not in group")

        await self.db.commit()
        return {"message": "Student removed from group"}

    async def get_group_students(
        self, group_id: int, teacher_id: int
    ) -> list[dict]:
        group_result = await self.db.execute(
            select(Group).where(
                Group.id == group_id, Group.teacher_id == teacher_id
            )
        )
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        result = await self.db.execute(
            select(User)
            .join(GroupStudent, GroupStudent.student_id == User.id)
            .where(GroupStudent.group_id == group_id)
        )
        students = result.scalars().all()

        return [
            {"id": s.id, "name": s.full_name, "email": s.email} for s in students
        ]