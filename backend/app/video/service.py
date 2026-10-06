from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.lessons.models import Lesson
from app.shared.config import settings


class VideosService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_token(
        self, lesson_id: int, current_user: User
    ) -> dict:
        """Сгенерировать JWT для Jitsi-комнаты урока.

        Доступ: учитель или ученик урока.
        Учитель — moderator, ученик — обычный.
        """
        result = await self.db.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        if current_user.id not in (lesson.teacher_id, lesson.student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        is_moderator = current_user.id == lesson.teacher_id

        now = datetime.now(timezone.utc)
        exp = now + timedelta(hours=settings.JITSI_TOKEN_EXPIRE_HOURS)

        room = f"lesson-{lesson.id}"

        payload = {
            "aud": "jitsi",
            "iss": settings.JITSI_JWT_APP_ID,
            "sub": settings.JITSI_DOMAIN,
            "room": room,
            "exp": exp,
            "nbf": now,
            "iat": now,
            "context": {
                "user": {
                    "id": str(current_user.id),
                    "name": current_user.full_name,
                    "email": current_user.email,
                    "moderator": is_moderator,
                }
            },
        }

        token = jwt.encode(
            payload,
            settings.JITSI_JWT_APP_SECRET,
            algorithm="HS256",
        )

        return {
            "token": token,
            "domain": settings.JITSI_DOMAIN,
            "room": room,
        }