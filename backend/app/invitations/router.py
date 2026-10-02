from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.invitations.service import InvitationsService
from app.shared.db import get_db

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/generate")
async def generate_invitation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Сгенерировать ссылку-приглашение для ученика."""
    service = InvitationsService(db)
    return await service.generate(current_user.id)


@router.post("/validate/{code}")
async def validate_invitation(code: str, db: AsyncSession = Depends(get_db)):
    """Проверить, действительна ли ссылка-приглашение."""
    service = InvitationsService(db)
    return await service.validate(code)


@router.post("/accept/{code}")
async def accept_invitation(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Привязать залогиненного ученика к учителю по коду."""
    service = InvitationsService(db)
    return await service.accept(code, current_user)