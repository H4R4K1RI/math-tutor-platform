from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import secrets

from app.db.database import get_db
from app.models.user import User
from app.models.invitation import Invitation
from app.core.dependencies import get_current_teacher, get_current_user

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/generate")
async def generate_invitation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Сгенерировать ссылку-приглашение для ученика"""
    
    # Генерируем уникальный код
    code = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)  # ссылка действует 7 дней
    
    invitation = Invitation(
        teacher_id=current_user.id,
        code=code,
        expires_at=expires_at,
        is_used=False
    )
    
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    
    # Формируем ссылку для фронтенда
    invite_url = f"/register?invite={code}"
    
    return {
        "code": code,
        "url": invite_url,
        "expires_at": expires_at
    }


@router.post("/validate/{code}")
async def validate_invitation(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Проверить, действительна ли ссылка-приглашение"""
    
    result = await db.execute(
        select(Invitation).where(Invitation.code == code)
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invitation already used")
    
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation expired")
    
    # Получаем учителя
    teacher_result = await db.execute(
        select(User).where(User.id == invitation.teacher_id)
    )
    teacher = teacher_result.scalar_one_or_none()
    
    return {
        "valid": True,
        "teacher_id": invitation.teacher_id,
        "teacher_name": teacher.full_name if teacher else "Teacher"
    }


@router.post("/use/{code}")
async def use_invitation(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Привязать ученика к учителю после регистрации"""
    
    result = await db.execute(
        select(Invitation).where(Invitation.code == code)
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.is_used:
        raise HTTPException(status_code=400, detail="Invitation already used")
    
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation expired")
    
    # Отмечаем инвайт как использованный
    invitation.is_used = True
    invitation.email = current_user.email
    
    # Создаём чат между учителем и учеником
    from app.models.chat import Chat
    chat = Chat(
        teacher_id=invitation.teacher_id,
        student_id=current_user.id,
        assignment_id=None
    )
    db.add(chat)
    
    await db.commit()
    
    return {"message": "Successfully connected to teacher"}