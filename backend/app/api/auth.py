from datetime import datetime, timezone
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.email import (
    generate_verification_token,
    send_verification_email,
    verify_email_token,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.database import get_db
from app.models.chat import Chat
from app.models.invitation import Invitation
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse

if os.getenv("TESTING") == "1":
    limiter = Limiter(key_func=get_remote_address, enabled=False)
else:
    limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
@limiter.limit("20/hour")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # Проверяем, существует ли пользователь
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован",
        )

    # Для учеников — обязателен валидный инвайт
    invitation = None
    if user_data.role == "student":
        if not user_data.invite_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Регистрация ученика возможна только по приглашению от репетитора",
            )

        inv_result = await db.execute(
            select(Invitation).where(Invitation.code == user_data.invite_code)
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
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True,
        is_verified=True,  # временно: без подтверждения email
    )

    db.add(new_user)
    await db.flush()  # чтобы получить new_user.id

    # Если ученик — привязываем к учителю и помечаем инвайт использованным
    if user_data.role == "student" and invitation:
        invitation.is_used = True
        invitation.email = user_data.email

        # Создаём чат между учителем и учеником
        chat = Chat(
            teacher_id=invitation.teacher_id,
            student_id=new_user.id,
            assignment_id=None,
        )
        db.add(chat)

    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
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

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=30 * 60,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return {"message": "Вход выполнен успешно"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Выход выполнен успешно"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Подтверждение email по токену (JSON-ответ для SPA)."""

    email = verify_email_token(token)

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Недействительная или просроченная ссылка",
        )

    await db.execute(
        update(User).where(User.email == email).values(is_verified=True)
    )
    await db.commit()

    return {"message": "Email успешно подтверждён"}

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Обновление access токена через refresh token"""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    payload = decode_token(refresh_token, token_type="refresh")

    if not payload or not payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    result = await db.execute(select(User).where(User.id == payload.user_id))
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
    new_access_token = create_access_token(token_data)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=30 * 60,
        path="/",
    )

    return {"message": "Token refreshed"}