from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment, Submission
from app.assignments.schemas import (
    AssignmentCreate,
    AssignmentUpdate,
    SubmissionCreate,
    SubmissionUpdate,
)
from app.auth.models import User
from app.students.service import get_student_teacher_ids
from app.chat.models import Chat
from app.groups.models import Group, GroupStudent
from app.chat.socket import sio



class AssignmentsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, teacher_id: int, data: AssignmentCreate) -> dict:
        if data.group_id:
            group_result = await self.db.execute(
                select(Group).where(
                    Group.id == data.group_id,
                    Group.teacher_id == teacher_id,
                )
            )
            group = group_result.scalar_one_or_none()
            if not group:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to this group",
                )

            result = await self.db.execute(
                select(GroupStudent.student_id).where(
                    GroupStudent.group_id == data.group_id
                )
            )
            students_ids = [row[0] for row in result.all()]

            if not students_ids:
                raise HTTPException(
                    status_code=400,
                    detail="Group has no students",
                )

            created = []
            for student_id in students_ids:
                new_a = Assignment(
                    title=data.title,
                    description=data.description,
                    attachments=data.attachments,
                    due_date=data.due_date,
                    teacher_id=teacher_id,
                    student_id=student_id,
                    group_id=data.group_id,
                )
                self.db.add(new_a)
                created.append(new_a)

            await self.db.commit()
            for a in created:
                await self.db.refresh(a)

            await sio.emit(
                "assignment_updated",
                {
                    "action": "created",
                    "assignment_ids": [a.id for a in created],
                    "count": len(created),
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
                    for a in created
                ],
                "count": len(created),
            }

        new_a = Assignment(
            title=data.title,
            description=data.description,
            attachments=data.attachments,
            due_date=data.due_date,
            teacher_id=teacher_id,
            student_id=data.student_id,
            group_id=None,
        )
        self.db.add(new_a)
        await self.db.commit()
        await self.db.refresh(new_a)

        await sio.emit(
            "assignment_updated",
            {"action": "created", "assignment_id": new_a.id},
        )

        return {
            "assignments": [
                {
                    "id": new_a.id,
                    "title": new_a.title,
                    "description": new_a.description,
                    "attachments": new_a.attachments,
                    "due_date": new_a.due_date.isoformat() if new_a.due_date else None,
                    "teacher_id": new_a.teacher_id,
                    "student_id": new_a.student_id,
                    "group_id": new_a.group_id,
                    "created_at": new_a.created_at.isoformat() if new_a.created_at else None,
                }
            ],
            "count": 1,
        }

    async def get_list(
        self, current_user: User, skip: int, limit: int
    ) -> dict:
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
            teacher_ids = await get_student_teacher_ids(
                self.db, current_user.id
            )

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

        result = await self.db.execute(query.offset(skip).limit(limit))
        total_result = await self.db.execute(total_query)

        assignments = result.scalars().all()
        total = total_result.scalar()

        return {"items": assignments, "total": total, "skip": skip, "limit": limit}

    async def get_by_id(self, assignment_id: int, current_user: User) -> Assignment:
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
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
                teacher_ids = await get_student_teacher_ids(
                    self.db, current_user.id
                )
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

    async def update(
        self, assignment_id: int, teacher_id: int, data: AssignmentUpdate
    ) -> Assignment:
        result = await self.db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id,
                Assignment.teacher_id == teacher_id,
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assignment, field, value)

        submissions_result = await self.db.execute(
            select(Submission).where(Submission.assignment_id == assignment_id)
        )
        submissions = submissions_result.scalars().all()

        for sub in submissions:
            sub.status = "pending"
            sub.feedback = None

        await self.db.commit()

        await sio.emit(
            "assignment_updated",
            {"action": "updated", "assignment_id": assignment_id},
        )
        await self.db.refresh(assignment)

        return assignment

    async def delete(self, assignment_id: int, teacher_id: int) -> dict:
        result = await self.db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id,
                Assignment.teacher_id == teacher_id,
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )

        await self.db.delete(assignment)
        await self.db.commit()

        await sio.emit(
            "assignment_deleted",
            {"action": "deleted", "assignment_id": assignment_id},
        )

        return {"message": "Assignment deleted successfully"}


class SubmissionsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, current_user: User, data: SubmissionCreate
    ) -> Submission:
        if current_user.role == "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers cannot submit solutions",
            )

        result = await self.db.execute(
            select(Assignment).where(Assignment.id == data.assignment_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found",
            )

        if assignment.student_id not in (None, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this assignment",
            )

        result = await self.db.execute(
            select(Submission).where(
                (Submission.assignment_id == data.assignment_id)
                & (Submission.student_id == current_user.id)
            )
        )
        existing_submission = result.scalar_one_or_none()

        if existing_submission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted a solution for this assignment",
            )

        new_sub = Submission(
            content=data.content,
            files=data.files,
            assignment_id=data.assignment_id,
            student_id=current_user.id,
            status="pending",
        )

        self.db.add(new_sub)
        await self.db.commit()
        await self.db.refresh(new_sub)

        await sio.emit(
            "submission_updated",
            {
                "action": "submitted",
                "submission_id": new_sub.id,
                "assignment_id": new_sub.assignment_id,
            },
        )

        return new_sub

    async def get_list(
        self,
        current_user: User,
        skip: int,
        limit: int,
        assignment_id: int | None = None,
    ) -> dict:
        if current_user.role == "teacher":
            query = (
                select(Submission)
                .join(Assignment, Submission.assignment_id == Assignment.id)
                .where(Assignment.teacher_id == current_user.id)
                .order_by(Submission.submitted_at)
            )
            total_query = (
                select(func.count())
                .select_from(Submission)
                .join(Assignment, Submission.assignment_id == Assignment.id)
                .where(Assignment.teacher_id == current_user.id)
            )

            if assignment_id:
                query = query.where(Submission.assignment_id == assignment_id)
                total_query = total_query.where(
                    Submission.assignment_id == assignment_id
                )
        else:
            query = select(Submission).where(
                Submission.student_id == current_user.id
            )
            total_query = (
                select(func.count())
                .where(Submission.student_id == current_user.id)
                .select_from(Submission)
            )

            if assignment_id:
                query = query.where(Submission.assignment_id == assignment_id)
                total_query = total_query.where(
                    Submission.assignment_id == assignment_id
                )

        result = await self.db.execute(query.offset(skip).limit(limit))
        total_result = await self.db.execute(total_query)

        submissions = result.scalars().all()
        total = total_result.scalar()

        return {
            "items": submissions,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_by_id(
        self, submission_id: int, current_user: User
    ) -> Submission:
        result = await self.db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found",
            )

        if current_user.role == "teacher":
            assignment_result = await self.db.execute(
                select(Assignment).where(
                    Assignment.id == submission.assignment_id
                )
            )
            assignment = assignment_result.scalar_one_or_none()
            if not assignment or assignment.teacher_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this submission",
                )
        else:
            if submission.student_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this submission",
                )

        return submission

    async def update(
        self, submission_id: int, current_user: User, data: SubmissionUpdate
    ) -> Submission:
        result = await self.db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found",
            )

        if current_user.role == "teacher":
            assignment_result = await self.db.execute(
                select(Assignment).where(
                    Assignment.id == submission.assignment_id
                )
            )
            assignment = assignment_result.scalar_one_or_none()
            if not assignment or assignment.teacher_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this submission",
                )

            if data.status is not None:
                submission.status = data.status
            if data.feedback is not None:
                submission.feedback = data.feedback
        elif submission.student_id == current_user.id:
            if data.content is not None:
                submission.content = data.content
            if data.files is not None:
                submission.files = data.files
            if data.content is not None or data.files is not None:
                submission.status = "pending"
                submission.feedback = None
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this submission",
            )

        await self.db.commit()

        await sio.emit(
            "submission_updated",
            {
                "action": "reviewed",
                "submission_id": submission.id,
                "assignment_id": submission.assignment_id,
                "status": submission.status,
            },
        )
        await self.db.refresh(submission)

        return submission

    async def delete(self, submission_id: int, current_user: User) -> dict:
        result = await self.db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found",
            )

        if current_user.role == "teacher":
            assignment_result = await self.db.execute(
                select(Assignment).where(
                    Assignment.id == submission.assignment_id
                )
            )
            assignment = assignment_result.scalar_one_or_none()
            if not assignment or assignment.teacher_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this submission",
                )
        elif submission.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this submission",
            )

        await self.db.delete(submission)
        await self.db.commit()

        return {"message": "Submission deleted successfully"}