from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.models import Chat
from app.chat.socket import sio
from app.lessons.models import Lesson, LessonRequest
from app.lessons.schemas import (
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    LessonRequestCreate,
    LessonRequestUpdate,
)
from app.models.payment import Payment, StudentBalance
from app.shared.logger import logger


# ==================== LESSONS ====================


class LessonsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_lesson(
        self, data: LessonCreate, current_user: User
    ) -> Lesson:
        """Создать урок с автосписанием с баланса."""

        student_result = await self.db.execute(
            select(User).where(
                User.id == data.student_id, User.role == "student"
            )
        )
        student = student_result.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        if data.start_time < datetime.now().astimezone():
            raise HTTPException(
                status_code=400, detail="Cannot create lesson in the past"
            )

        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=400, detail="End time must be after start time"
            )

        balance_result = await self.db.execute(
            select(StudentBalance)
            .where(
                StudentBalance.student_id == data.student_id,
                StudentBalance.teacher_id == current_user.id,
            )
            .with_for_update()
        )
        balance = balance_result.scalar_one_or_none()
        current_balance = balance.balance if balance else Decimal("0")

        if data.price > 0 and current_balance < data.price:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно средств на балансе. Доступно: {current_balance} ₽, стоимость урока: {data.price} ₽",
            )

        new_lesson = Lesson(
            teacher_id=current_user.id,
            student_id=data.student_id,
            title=data.title,
            start_time=data.start_time,
            end_time=data.end_time,
            price=data.price,
            notes=data.notes,
        )

        self.db.add(new_lesson)

        if data.price > 0:
            if balance:
                balance.balance -= data.price
            else:
                balance = StudentBalance(
                    student_id=data.student_id,
                    teacher_id=current_user.id,
                    balance=-data.price,
                )
                self.db.add(balance)

            payment = Payment(
                student_id=data.student_id,
                teacher_id=current_user.id,
                amount=-data.price,
                note=f"Списание за урок: {new_lesson.title or 'Урок'} от {new_lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
            )
            self.db.add(payment)

        await self.db.commit()
        await self.db.refresh(new_lesson)

        return new_lesson

    async def get_lessons(
        self,
        current_user: User,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        status_filter: str | None = None,
    ) -> list[LessonResponse]:
        query = select(Lesson)

        if current_user.role == "teacher":
            query = query.where(Lesson.teacher_id == current_user.id)
        else:
            query = query.where(Lesson.student_id == current_user.id)

        if start_date:
            query = query.where(Lesson.start_time >= start_date)
        if end_date:
            query = query.where(Lesson.end_time <= end_date)
        if status_filter:
            query = query.where(Lesson.status == status_filter)

        query = query.order_by(Lesson.start_time)

        result = await self.db.execute(query)
        lessons = result.scalars().all()

        if not lessons:
            return []

        if current_user.role == "teacher":
            user_ids = {lesson.student_id for lesson in lessons}
        else:
            user_ids = {lesson.teacher_id for lesson in lessons}

        users_result = await self.db.execute(
            select(User).where(User.id.in_(user_ids))
        )
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

    async def update_lesson(
        self, lesson_id: int, data: LessonUpdate, current_user: User
    ) -> Lesson:
        """Обновить урок.

        При изменении price — корректируем баланс ученика и пишем Payment.
        """

        result = await self.db.execute(
            select(Lesson).where(
                Lesson.id == lesson_id, Lesson.teacher_id == current_user.id
            )
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        old_price = lesson.price

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lesson, field, value)

        new_price = lesson.price
        if "price" in update_data and old_price != new_price:
            price_diff = new_price - old_price

            balance_result = await self.db.execute(
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
                self.db.add(balance)

            if price_diff != 0:
                payment = Payment(
                    student_id=lesson.student_id,
                    teacher_id=lesson.teacher_id,
                    amount=-price_diff,
                    note=f"Корректировка цены урока: {lesson.title or 'Урок'} от {lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
                )
                self.db.add(payment)

        await self.db.commit()
        await self.db.refresh(lesson)

        return lesson

    async def delete_lesson(self, lesson_id: int, current_user: User) -> dict:
        """Отменить урок (с возвратом денег, если урок был платным)."""

        result = await self.db.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        if current_user.role == "teacher" and lesson.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        if (
            current_user.role == "student"
            and lesson.student_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        if lesson.status == "completed":
            raise HTTPException(
                status_code=400,
                detail="Нельзя отменить завершённый урок",
            )

        if lesson.price > 0:
            balance_result = await self.db.execute(
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
                self.db.add(balance)

            refund_payment = Payment(
                student_id=lesson.student_id,
                teacher_id=lesson.teacher_id,
                amount=lesson.price,
                note=f"Возврат за отменённый урок: {lesson.title or 'Урок'} от {lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
            )
            self.db.add(refund_payment)

        await self.db.delete(lesson)
        await self.db.commit()

        return {"message": "Lesson cancelled"}


# ==================== LESSON REQUESTS ====================


class LessonRequestsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(
        self, data: LessonRequestCreate, current_user: User
    ) -> LessonRequest:
        """Создать заявку на урок (только ученик)."""

        if current_user.role != "student":
            raise HTTPException(
                status_code=403,
                detail="Only students can create lesson requests",
            )

        teacher_result = await self.db.execute(
            select(User).where(
                User.id == data.teacher_id, User.role == "teacher"
            )
        )
        teacher = teacher_result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

        chat_result = await self.db.execute(
            select(Chat).where(
                Chat.teacher_id == data.teacher_id,
                Chat.student_id == current_user.id,
            )
        )
        if not chat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=403,
                detail="You are not connected to this teacher",
            )

        if data.start_time < datetime.now().astimezone():
            raise HTTPException(
                status_code=400, detail="Cannot request lesson in the past"
            )

        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=400, detail="End time must be after start time"
            )

        existing_request = await self.db.execute(
            select(LessonRequest).where(
                LessonRequest.teacher_id == data.teacher_id,
                LessonRequest.student_id == current_user.id,
                LessonRequest.start_time == data.start_time,
                LessonRequest.status == "pending",
            )
        )
        if existing_request.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="You already have a pending request for this time",
            )

        existing_lesson = await self.db.execute(
            select(Lesson).where(
                Lesson.teacher_id == data.teacher_id,
                Lesson.start_time == data.start_time,
            )
        )
        if existing_lesson.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="This time slot is already booked"
            )

        new_request = LessonRequest(
            teacher_id=data.teacher_id,
            student_id=current_user.id,
            title=data.title,
            start_time=data.start_time,
            end_time=data.end_time,
            notes=data.notes,
        )

        self.db.add(new_request)
        await self.db.commit()
        await self.db.refresh(new_request)

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

    async def get_requests(
        self, current_user: User, status_filter: str | None = None
    ) -> list[dict]:
        if current_user.role == "teacher":
            query = select(LessonRequest).where(
                LessonRequest.teacher_id == current_user.id
            )
        else:
            query = select(LessonRequest).where(
                LessonRequest.student_id == current_user.id
            )

        if status_filter:
            query = query.where(LessonRequest.status == status_filter)

        query = query.order_by(LessonRequest.created_at.desc())

        result = await self.db.execute(query)
        requests = result.scalars().all()

        if not requests:
            return []

        if current_user.role == "teacher":
            user_ids = {req.student_id for req in requests}
        else:
            user_ids = {req.teacher_id for req in requests}

        users_result = await self.db.execute(
            select(User).where(User.id.in_(user_ids))
        )
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
                    "student_name": (
                        other_user.full_name if other_user else "Unknown"
                    ),
                    "title": req.title,
                    "start_time": req.start_time,
                    "end_time": req.end_time,
                    "status": req.status,
                    "notes": req.notes,
                    "created_at": req.created_at,
                }
            )

        return response

    async def update_request(
        self, request_id: int, data: LessonRequestUpdate, current_user: User
    ) -> dict:
        """Подтвердить или отклонить заявку (только учитель)."""

        result = await self.db.execute(
            select(LessonRequest).where(
                LessonRequest.id == request_id,
                LessonRequest.teacher_id == current_user.id,
            )
        )
        lesson_request = result.scalar_one_or_none()

        if not lesson_request:
            raise HTTPException(status_code=404, detail="Request not found")

        if lesson_request.status != "pending":
            raise HTTPException(
                status_code=400, detail="Request already processed"
            )

        lesson_request.status = data.status

        if data.status == "approved":
            price = (
                data.price if data.price is not None else Decimal("0")
            )

            if price > 0:
                balance_result = await self.db.execute(
                    select(StudentBalance)
                    .where(
                        StudentBalance.student_id
                        == lesson_request.student_id,
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
            self.db.add(new_lesson)

            if price > 0:
                balance_result = await self.db.execute(
                    select(StudentBalance)
                    .where(
                        StudentBalance.student_id
                        == lesson_request.student_id,
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
                    self.db.add(balance)

                payment = Payment(
                    student_id=lesson_request.student_id,
                    teacher_id=current_user.id,
                    amount=-price,
                    note=f"Списание за урок: {new_lesson.title or 'Урок'} от {new_lesson.start_time.strftime('%d.%m.%Y %H:%M')}",
                )
                self.db.add(payment)

            await self.db.commit()
            await self.db.refresh(new_lesson)

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
                logger.error(
                    f"Failed to emit lesson_request_approved: {e}"
                )
        else:
            await self.db.commit()

        return {"message": f"Request {data.status}"}