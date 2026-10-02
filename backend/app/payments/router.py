from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.payments.schemas import PaymentCreate
from app.payments.service import PaymentsService
from app.shared.db import get_db

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/")
async def add_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Добавить платёж от ученика."""
    service = PaymentsService(db)
    return await service.add_payment(payment_data, current_user)


@router.get("/students")
async def get_students_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Баланс всех учеников учителя."""
    service = PaymentsService(db)
    return await service.get_students_balance(current_user)


@router.get("/my-balances")
async def get_my_balances(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Балансы ученика по каждому учителю."""
    service = PaymentsService(db)
    return await service.get_my_balances(current_user)


@router.get("/history/{student_id}")
async def get_payment_history(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """История платежей ученика."""
    service = PaymentsService(db)
    return await service.get_payment_history(student_id, current_user)