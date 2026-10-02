import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.shared.db import get_db
from app.models.chat import Chat
from app.models.invitation import Invitation
from app.auth.models import User

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/generate")
async def generate_invitation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Сгенерировать ссылку-приглашение для ученика"""

    code = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = Invitation(
        teacher_id=current_user.id, code=code, expires_at=expires_at, is_used=False
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    invite_url = f"/register?invite={code}"

    return {"code": code, "url": invite_url, "expires_at": expires_at}


@router.post("/validate/{code}")
async def validate_invitation(code: str, db: AsyncSession = Depends(get_db)):
    """Проверить, действительна ли ссылка-приглашение"""

    result = await db.execute(select(Invitation).where(Invitation.code == code))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invitation already used")

    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation expired")

    teacher_result = await db.execute(
        select(User).where(User.id == invitation.teacher_id)
    )
    teacher = teacher_result.scalar_one_or_none()

    return {
        "valid": True,
        "teacher_id": invitation.teacher_id,
        "teacher_name": teacher.full_name if teacher else "Teacher",
    }


@router.post("/accept/{code}")
async def accept_invitation(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Привязать залогиненного ученика к учителю по коду"""

    if current_user.role != "student":
        raise HTTPException(
            status_code=403, detail="Only students can accept invitations"
        )

    result = await db.execute(select(Invitation).where(Invitation.code == code))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invitation already used")

    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation expired")

    # Проверяем, что ученик ещё не связан с учителем
    chat_result = await db.execute(
        select(Chat).where(
            Chat.teacher_id == invitation.teacher_id,
            Chat.student_id == current_user.id,
        )
    )
    if chat_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already connected")

    invitation.is_used = True
    invitation.email = current_user.email

    chat = Chat(
        teacher_id=invitation.teacher_id,
        student_id=current_user.id,
        assignment_id=None,
    )
    db.add(chat)

    await db.commit()

    return {"message": "Successfully connected to teacher"}