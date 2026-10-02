import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.models import Chat
from app.models.invitation import Invitation


class InvitationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, teacher_id: int) -> dict:
        """Генерирует инвайт-код для учителя."""
        code = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        invitation = Invitation(
            teacher_id=teacher_id,
            code=code,
            expires_at=expires_at,
            is_used=False,
        )

        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        invite_url = f"/register?invite={code}"

        return {"code": code, "url": invite_url, "expires_at": expires_at}

    async def validate(self, code: str) -> dict:
        """Проверяет, действителен ли код."""
        result = await self.db.execute(
            select(Invitation).where(Invitation.code == code)
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if invitation.is_used:
            raise HTTPException(status_code=400, detail="Invitation already used")

        if invitation.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Invitation expired")

        teacher_result = await self.db.execute(
            select(User).where(User.id == invitation.teacher_id)
        )
        teacher = teacher_result.scalar_one_or_none()

        return {
            "valid": True,
            "teacher_id": invitation.teacher_id,
            "teacher_name": teacher.full_name if teacher else "Teacher",
        }

    async def accept(self, code: str, student: User) -> dict:
        """Привязывает залогиненного ученика к учителю."""
        if student.role != "student":
            raise HTTPException(
                status_code=403, detail="Only students can accept invitations"
            )

        result = await self.db.execute(
            select(Invitation).where(Invitation.code == code)
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if invitation.is_used:
            raise HTTPException(status_code=400, detail="Invitation already used")

        if invitation.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Invitation expired")

        # Проверяем, что ученик ещё не связан с учителем
        chat_result = await self.db.execute(
            select(Chat).where(
                Chat.teacher_id == invitation.teacher_id,
                Chat.student_id == student.id,
            )
        )
        if chat_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Already connected")

        invitation.is_used = True
        invitation.email = student.email

        chat = Chat(
            teacher_id=invitation.teacher_id,
            student_id=student.id,
            assignment_id=None,
        )
        self.db.add(chat)

        await self.db.commit()

        return {"message": "Successfully connected to teacher"}