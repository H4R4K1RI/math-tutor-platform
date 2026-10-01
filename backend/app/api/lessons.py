from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_teacher, get_current_user
from app.db.database import get_db
from app.models.lesson import Lesson
from app.models.payment import Payment, StudentBalance
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/", response_model=LessonResponse)
async def create_lesson(
    lesson_data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создать урок (только учитель) с автосписанием с баланса"""

    student_result = await db.execute(
        select(User).where(User.id == lesson_data.student_id, User.role == "student")
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if lesson_data.start_time < datetime.now().astimezone():
        raise HTTPException(status_code=400, detail="Cannot create lesson in the past")

    if lesson_data.end_time <= lesson_data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    balance_result = await db.execute(
        select(StudentBalance)
        .where(
            StudentBalance.student_id == lesson_data.student_id,
            StudentBalance.teacher_id == current_user.id,
        )
        .with_for_update()
    )
    balance = balance_result.scalar_one_or_none()
    current_balance = balance.balance if balance else Decimal("0")

    if lesson_data.price > 0 and current_balance < lesson_data.price:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно средств на балансе. Доступно: {current_balance} ₽, стоимость урока: {lesson_data.price} ₽",
        )

    new_lesson = Lesson(
        teacher_id=current_user.id,
        student_id=lesson_data.student_id,
        title=lesson_data.title,
        start_time=lesson_data.start_time,
        end_time=lesson_data.end_time,
        price=lesson_data.price,
        notes=lesson_data.notes,
    )

    db.add(new_lesson)

    if lesson_data.price > 0:
        if balance:
            balance.balance -= lesson_data.price
        else:
            balance = StudentBalance(
                student_id=lesson_data.student_id,
                teacher_id=current_user.id,
                balance=-lesson_data.price,
            )
            db.add(balance)

        payment = Payment(
            student_id=lesson_data.student_id,
            teacher_id=current_user.id,
            amount=-lesson_data.price,
            note=f"Списание за урок: {new_lesson.title or 'Урок'} от {new_lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
        )
        db.add(payment)

    await db.commit()
    await db.refresh(new_lesson)

    return new_lesson


@router.get("/", response_model=List[LessonResponse])
async def get_lessons(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить уроки пользователя (оптимизировано)"""

    query = select(Lesson)

    if current_user.role == "teacher":
        query = query.where(Lesson.teacher_id == current_user.id)
    else:
        query = query.where(Lesson.student_id == current_user.id)

    if start_date:
        query = query.where(Lesson.start_time >= start_date)
    if end_date:
        query = query.where(Lesson.end_time <= end_date)
    if status:
        query = query.where(Lesson.status == status)

    query = query.order_by(Lesson.start_time)

    result = await db.execute(query)
    lessons = result.scalars().all()

    if not lessons:
        return []

    # Собираем все user_id, которые нужно подгрузить
    if current_user.role == "teacher":
        user_ids = {lesson.student_id for lesson in lessons}
    else:
        user_ids = {lesson.teacher_id for lesson in lessons}

    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    response = []
    for lesson in lessons:
        if current_user.role == "teacher":
            other_user = users_map.get(lesson.student_id)
        else:
            other_user = users_map.get(lesson.teacher_id)

        response.append(
            LessonResponse(
                **lesson.__dict__,
                student_name=other_user.full_name if other_user else None,
            )
        )

    return response


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить урок (только учитель).

    При изменении price — корректируем баланс ученика и пишем Payment.
    """

    result = await db.execute(
        select(Lesson).where(
            Lesson.id == lesson_id, Lesson.teacher_id == current_user.id
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    old_price = lesson.price

    update_data = lesson_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)

    new_price = lesson.price
    if "price" in update_data and old_price != new_price:
        price_diff = new_price - old_price

        balance_result = await db.execute(
            select(StudentBalance)
            .where(
                StudentBalance.student_id == lesson.student_id,
                StudentBalance.teacher_id == lesson.teacher_id,
            )
            .with_for_update()
        )
        balance = balance_result.scalar_one_or_none()

        if balance:
            balance.balance -= price_diff
        else:
            balance = StudentBalance(
                student_id=lesson.student_id,
                teacher_id=lesson.teacher_id,
                balance=-price_diff,
            )
            db.add(balance)

        if price_diff != 0:
            payment = Payment(
                student_id=lesson.student_id,
                teacher_id=lesson.teacher_id,
                amount=-price_diff,
                note=f"Корректировка цены урока: {lesson.title or 'Урок'} от {lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
            )
            db.add(payment)

    await db.commit()
    await db.refresh(lesson)

    return lesson


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отменить урок (с возвратом денег, если урок был платным)"""

    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if current_user.role == "teacher" and lesson.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "student" and lesson.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if lesson.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Нельзя отменить завершённый урок",
        )

    if lesson.price > 0:
        balance_result = await db.execute(
            select(StudentBalance)
            .where(
                StudentBalance.student_id == lesson.student_id,
                StudentBalance.teacher_id == lesson.teacher_id,
            )
            .with_for_update()
        )
        balance = balance_result.scalar_one_or_none()
        if balance:
            balance.balance += lesson.price
        else:
            balance = StudentBalance(
                student_id=lesson.student_id,
                teacher_id=lesson.teacher_id,
                balance=lesson.price,
            )
            db.add(balance)

        refund_payment = Payment(
            student_id=lesson.student_id,
            teacher_id=lesson.teacher_id,
            amount=lesson.price,
            note=f"Возврат за отменённый урок: {lesson.title or 'Урок'} от {lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
        )
        db.add(refund_payment)

    await db.delete(lesson)
    await db.commit()

    return {"message": "Lesson cancelled"}