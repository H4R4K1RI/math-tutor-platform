from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.schemas import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    SubmissionCreate,
    SubmissionResponse,
    SubmissionUpdate,
)
from app.assignments.service import AssignmentsService, SubmissionsService
from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.shared.db import get_db

router = APIRouter(tags=["assignments"])


# ==================== ASSIGNMENTS ====================


@router.post("/assignments/")
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = AssignmentsService(db)
    return await service.create(current_user.id, assignment_data)


@router.get("/assignments/")
async def get_assignments(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AssignmentsService(db)
    return await service.get_list(current_user, skip, limit)


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AssignmentsService(db)
    return await service.get_by_id(assignment_id, current_user)


@router.put("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = AssignmentsService(db)
    return await service.update(assignment_id, current_user.id, assignment_data)


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    service = AssignmentsService(db)
    return await service.delete(assignment_id, current_user.id)


# ==================== SUBMISSIONS ====================


@router.post("/submissions/", response_model=SubmissionResponse)
async def create_submission(
    submission_data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SubmissionsService(db)
    return await service.create(current_user, submission_data)


@router.get("/submissions/")
async def get_submissions(
    skip: int = 0,
    limit: int = 10,
    assignment_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SubmissionsService(db)
    return await service.get_list(current_user, skip, limit, assignment_id)


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SubmissionsService(db)
    return await service.get_by_id(submission_id, current_user)


@router.put("/submissions/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: int,
    submission_data: SubmissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SubmissionsService(db)
    return await service.update(submission_id, current_user, submission_data)


@router.delete("/submissions/{submission_id}")
async def delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SubmissionsService(db)
    return await service.delete(submission_id, current_user)