from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserCreate, UserLogin
from app.shared.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.chat.models import Chat
from app.invitations.models import Invitation


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserCreate) -> User:
        # Проверяем, существует ли пользователь
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже зарегистрирован",
            )

        # Для учеников — обязателен валидный инвайт
        invitation = None
        if data.role == "student":
            if not data.invite_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Регистрация ученика возможна только по приглашению от репетитора",
                )

            inv_result = await self.db.execute(
                select(Invitation).where(Invitation.code == data.invite_code)
            )
            invitation = inv_result.scalar_one_or_none()

            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Недействительная ссылка-приглашение",
                )

            if invitation.is_used:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Это приглашение уже использовано",
                )

            if invitation.expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Срок действия приглашения истёк",
                )

        # Создаём нового пользователя
        new_user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=get_password_hash(data.password),
            role=data.role,
            is_active=True,
            is_verified=True,  # временно: без подтверждения email
        )

        self.db.add(new_user)
        await self.db.flush()  # чтобы получить new_user.id

        # Если ученик — привязываем к учителю и помечаем инвайт использованным
        if data.role == "student" and invitation:
            invitation.is_used = True
            invitation.email = data.email

            chat = Chat(
                teacher_id=invitation.teacher_id,
                student_id=new_user.id,
                assignment_id=None,
            )
            self.db.add(chat)

        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def login(self, data: UserLogin) -> tuple[User, str, str]:
        """Возвращает (user, access_token, refresh_token)."""
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Аккаунт пользователя отключён",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email не подтверждён. Проверьте почту и перейдите по ссылке",
            )

        token_data = {
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "type": "access",
        }
        access_token = create_access_token(token_data)

        refresh_data = {
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "type": "refresh",
        }
        refresh_token = create_refresh_token(refresh_data)

        return user, access_token, refresh_token

    async def refresh(self, refresh_token_value: str) -> str:
        """Возвращает новый access_token."""
        from app.shared.security import decode_token

        payload = decode_token(refresh_token_value, token_type="refresh")

        if not payload or not payload.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        result = await self.db.execute(
            select(User).where(User.id == payload.user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        token_data = {
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "type": "access",
        }
        return create_access_token(token_data)