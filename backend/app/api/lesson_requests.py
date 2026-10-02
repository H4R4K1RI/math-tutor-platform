from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.shared.logger import logger
from app.shared.db import get_db
from app.models.chat import Chat
from app.models.lesson import Lesson
from app.models.lesson_request import LessonRequest
from app.models.payment import Payment, StudentBalance
from app.auth.models import User
from app.schemas.lesson_request import (
    LessonRequestCreate,
    LessonRequestResponse,
    LessonRequestUpdate,
)
from app.socket_manager import sio

router = APIRouter(prefix="/lesson-requests", tags=["lesson-requests"])


@router.post("/", response_model=LessonRequestResponse)
async def create_lesson_request(
    request_data: LessonRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создать заявку на урок (только ученик)"""

    if current_user.role != "student":
        raise HTTPException(
            status_code=403, detail="Only students can create lesson requests"
        )

    teacher_result = await db.execute(
        select(User).where(User.id == request_data.teacher_id, User.role == "teacher")
    )
    teacher = teacher_result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    chat_result = await db.execute(
        select(Chat).where(
            Chat.teacher_id == request_data.teacher_id,
            Chat.student_id == current_user.id,
        )
    )
    if not chat_result.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="You are not connected to this teacher",
        )

    if request_data.start_time < datetime.now().astimezone():
        raise HTTPException(status_code=400, detail="Cannot request lesson in the past")

    if request_data.end_time <= request_data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    existing_request = await db.execute(
        select(LessonRequest).where(
            LessonRequest.teacher_id == request_data.teacher_id,
            LessonRequest.student_id == current_user.id,
            LessonRequest.start_time == request_data.start_time,
            LessonRequest.status == "pending",
        )
    )
    if existing_request.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="You already have a pending request for this time"
        )

    existing_lesson = await db.execute(
        select(Lesson).where(
            Lesson.teacher_id == request_data.teacher_id,
            Lesson.start_time == request_data.start_time,
        )
    )
    if existing_lesson.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This time slot is already booked")

    new_request = LessonRequest(
        teacher_id=request_data.teacher_id,
        student_id=current_user.id,
        title=request_data.title,
        start_time=request_data.start_time,
        end_time=request_data.end_time,
        notes=request_data.notes,
    )

    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    try:
        await sio.emit(
            "new_lesson_request",
            {
                "request_id": new_request.id,
                "student_name": current_user.full_name,
                "start_time": new_request.start_time.isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"Failed to emit new_lesson_request: {e}")

    return new_request


@router.get("/", response_model=List[LessonRequestResponse])
async def get_lesson_requests(
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить заявки на урок (оптимизировано)"""

    if current_user.role == "teacher":
        query = select(LessonRequest).where(
            LessonRequest.teacher_id == current_user.id
        )
    else:
        query = select(LessonRequest).where(
            LessonRequest.student_id == current_user.id
        )

    if status:
        query = query.where(LessonRequest.status == status)

    query = query.order_by(LessonRequest.created_at.desc())

    result = await db.execute(query)
    requests = result.scalars().all()

    if not requests:
        return []

    # Собираем ID пользователей для подгрузки
    if current_user.role == "teacher":
        user_ids = {req.student_id for req in requests}
    else:
        user_ids = {req.teacher_id for req in requests}

    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    response = []
    for req in requests:
        if current_user.role == "teacher":
            other_user = users_map.get(req.student_id)
        else:
            other_user = users_map.get(req.teacher_id)

        response.append(
            {
                "id": req.id,
                "teacher_id": req.teacher_id,
                "student_id": req.student_id,
                "student_name": other_user.full_name if other_user else "Unknown",
                "title": req.title,
                "start_time": req.start_time,
                "end_time": req.end_time,
                "status": req.status,
                "notes": req.notes,
                "created_at": req.created_at,
            }
        )

    return response


@router.put("/{request_id}")
async def update_lesson_request(
    request_id: int,
    update_data: LessonRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Подтвердить или отклонить заявку (только учитель)"""

    result = await db.execute(
        select(LessonRequest).where(
            LessonRequest.id == request_id,
            LessonRequest.teacher_id == current_user.id,
        )
    )
    lesson_request = result.scalar_one_or_none()

    if not lesson_request:
        raise HTTPException(status_code=404, detail="Request not found")

    if lesson_request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    lesson_request.status = update_data.status

    if update_data.status == "approved":
        price = update_data.price if update_data.price is not None else Decimal("0")

        if price > 0:
            balance_result = await db.execute(
                select(StudentBalance)
                .where(
                    StudentBalance.student_id == lesson_request.student_id,
                    StudentBalance.teacher_id == current_user.id,
                )
                .with_for_update()
            )
            balance = balance_result.scalar_one_or_none()
            current_balance = balance.balance if balance else Decimal("0")

            if current_balance < price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно средств на балансе ученика. Доступно: {current_balance} ₽, стоимость урока: {price} ₽",
                )

        new_lesson = Lesson(
            teacher_id=lesson_request.teacher_id,
            student_id=lesson_request.student_id,
            title=lesson_request.title,
            start_time=lesson_request.start_time,
            end_time=lesson_request.end_time,
            price=price,
            notes=lesson_request.notes,
            status="scheduled",
        )
        db.add(new_lesson)

        if price > 0:
            balance_result = await db.execute(
                select(StudentBalance)
                .where(
                    StudentBalance.student_id == lesson_request.student_id,
                    StudentBalance.teacher_id == current_user.id,
                )
                .with_for_update()
            )
            balance = balance_result.scalar_one_or_none()

            if balance:
                balance.balance -= price
            else:
                balance = StudentBalance(
                    student_id=lesson_request.student_id,
                    teacher_id=current_user.id,
                    balance=-price,
                )
                db.add(balance)

            payment = Payment(
                student_id=lesson_request.student_id,
                teacher_id=current_user.id,
                amount=-price,
                note=f"Списание за урок: {new_lesson.title or 'Урок'} от {new_lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
            )
            db.add(payment)

        await db.commit()
        await db.refresh(new_lesson)

        try:
            await sio.emit(
                "lesson_request_approved",
                {
                    "request_id": request_id,
                    "lesson_id": new_lesson.id,
                    "start_time": lesson_request.start_time.isoformat(),
                    "price": str(price),
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit lesson_request_approved: {e}")
    else:
        await db.commit()

    return {"message": f"Request {update_data.status}"}