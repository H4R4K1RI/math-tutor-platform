from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.shared.db import get_db
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.auth.models import User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionUpdate,
)
from app.socket_manager import sio

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=SubmissionResponse)
async def create_submission(
    submission_data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отправка решения (только для учеников)"""

    if current_user.role == "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers cannot submit solutions",
        )

    result = await db.execute(
        select(Assignment).where(Assignment.id == submission_data.assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    if assignment.student_id not in (None, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this assignment",
        )

    # Проверяем, не отправлял ли ученик уже решение
    result = await db.execute(
        select(Submission).where(
            (Submission.assignment_id == submission_data.assignment_id)
            & (Submission.student_id == current_user.id)
        )
    )
    existing_submission = result.scalar_one_or_none()

    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a solution for this assignment",
        )

    new_submission = Submission(
        content=submission_data.content,
        files=submission_data.files,
        assignment_id=submission_data.assignment_id,
        student_id=current_user.id,
        status="pending",
    )

    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)

    await sio.emit(
        "submission_updated",
        {
            "action": "submitted",
            "submission_id": new_submission.id,
            "assignment_id": new_submission.assignment_id,
        },
    )

    return new_submission


@router.get("/")
async def get_submissions(
    skip: int = 0,
    limit: int = 10,
    assignment_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить решения (учитель — только по своим заданиям, ученик — только свои)"""

    if current_user.role == "teacher":
        # Только решения по заданиям этого учителя
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
            total_query = total_query.where(Submission.assignment_id == assignment_id)
    else:
        query = select(Submission).where(Submission.student_id == current_user.id)
        total_query = (
            select(func.count())
            .where(Submission.student_id == current_user.id)
            .select_from(Submission)
        )

        if assignment_id:
            query = query.where(Submission.assignment_id == assignment_id)
            total_query = total_query.where(Submission.assignment_id == assignment_id)

    result = await db.execute(query.offset(skip).limit(limit))
    total_result = await db.execute(total_query)

    submissions = result.scalars().all()
    total = total_result.scalar()

    return {"items": submissions, "total": total, "skip": skip, "limit": limit}


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение деталей решения"""

    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    if current_user.role == "teacher":
        # Проверяем, что задание принадлежит учителю
        assignment_result = await db.execute(
            select(Assignment).where(Assignment.id == submission.assignment_id)
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


@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: int,
    submission_data: SubmissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление решения (учитель меняет статус/фидбек, ученик меняет content/files)"""

    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    if current_user.role == "teacher":
        # Проверяем, что задание принадлежит учителю
        assignment_result = await db.execute(
            select(Assignment).where(Assignment.id == submission.assignment_id)
        )
        assignment = assignment_result.scalar_one_or_none()
        if not assignment or assignment.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this submission",
            )

        if submission_data.status is not None:
            submission.status = submission_data.status
        if submission_data.feedback is not None:
            submission.feedback = submission_data.feedback
    elif submission.student_id == current_user.id:
        if submission_data.content is not None:
            submission.content = submission_data.content
        if submission_data.files is not None:
            submission.files = submission_data.files
        if submission_data.content is not None or submission_data.files is not None:
            submission.status = "pending"
            submission.feedback = None
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this submission",
        )

    await db.commit()

    await sio.emit(
        "submission_updated",
        {
            "action": "reviewed",
            "submission_id": submission.id,
            "assignment_id": submission.assignment_id,
            "status": submission.status,
        },
    )
    await db.refresh(submission)

    return submission


@router.delete("/{submission_id}")
async def delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление решения (только для учителя или автора)"""

    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    if current_user.role == "teacher":
        assignment_result = await db.execute(
            select(Assignment).where(Assignment.id == submission.assignment_id)
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

    await db.delete(submission)
    await db.commit()

    return {"message": "Submission deleted successfully"}