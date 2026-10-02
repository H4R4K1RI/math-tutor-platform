import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select

from app.auth.models import User
from app.lessons.models import Lesson
from app.notifications.email_service import (
    send_payment_reminder_email,
    send_reminder_email,
)
from app.notifications.models import SentReminder
from app.payments.models import StudentBalance
from app.shared.db import AsyncSessionLocal
from app.shared.logger import logger

# Таймзона для планировщика
MSK = ZoneInfo("Europe/Moscow")


async def _was_sent(
    db, user_id: int, reminder_type: str, entity_id: int
) -> bool:
    """Проверяет, было ли уже отправлено такое напоминание."""
    result = await db.execute(
        select(SentReminder).where(
            SentReminder.user_id == user_id,
            SentReminder.reminder_type == reminder_type,
            SentReminder.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def _mark_sent(db, user_id: int, reminder_type: str, entity_id: int):
    """Помечает напоминание как отправленное."""
    db.add(
        SentReminder(
            user_id=user_id,
            reminder_type=reminder_type,
            entity_id=entity_id,
        )
    )


async def check_and_send_reminders():
    """Проверить расписание и отправить напоминания (с защитой от дублей).

    Все вычисления «сегодня/завтра/через час» — в МСК.
    """

    async with AsyncSessionLocal() as db:
        now = datetime.now(MSK)
        tomorrow = now + timedelta(days=1)
        tomorrow_start = tomorrow.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        tomorrow_end = tomorrow.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        one_hour_later = now + timedelta(hours=1)
        one_hour_start = one_hour_later - timedelta(minutes=5)
        one_hour_end = one_hour_later + timedelta(minutes=5)

        # 1. Напоминания за день до урока
        day_before_lessons = await db.execute(
            select(Lesson).where(
                Lesson.start_time >= tomorrow_start,
                Lesson.start_time <= tomorrow_end,
                Lesson.status == "scheduled",
            )
        )
        day_lessons = day_before_lessons.scalars().all()

        if day_lessons:
            student_ids = {l.student_id for l in day_lessons}
            students_result = await db.execute(
                select(User).where(User.id.in_(student_ids))
            )
            students_map = {u.id: u for u in students_result.scalars().all()}

            for lesson in day_lessons:
                student = students_map.get(lesson.student_id)
                if not student or not student.email:
                    continue

                if await _was_sent(db, student.id, "day_before", lesson.id):
                    continue

                await send_reminder_email(
                    to_email=student.email,
                    student_name=student.full_name,
                    lesson_title=lesson.title,
                    start_time=lesson.start_time,
                    reminder_type="day_before",
                )

                await _mark_sent(db, student.id, "day_before", lesson.id)

        # 2. Напоминания за час до урока
        hour_before_lessons = await db.execute(
            select(Lesson).where(
                Lesson.start_time >= one_hour_start,
                Lesson.start_time <= one_hour_end,
                Lesson.status == "scheduled",
            )
        )
        hour_lessons = hour_before_lessons.scalars().all()

        if hour_lessons:
            student_ids = {l.student_id for l in hour_lessons}
            students_result = await db.execute(
                select(User).where(User.id.in_(student_ids))
            )
            students_map = {u.id: u for u in students_result.scalars().all()}

            for lesson in hour_lessons:
                student = students_map.get(lesson.student_id)
                if not student or not student.email:
                    continue

                if await _was_sent(db, student.id, "hour_before", lesson.id):
                    continue

                await send_reminder_email(
                    to_email=student.email,
                    student_name=student.full_name,
                    lesson_title=lesson.title,
                    start_time=lesson.start_time,
                    reminder_type="hour_before",
                )

                await _mark_sent(db, student.id, "hour_before", lesson.id)

        # 3. Напоминания об оплате (только раз в сутки на студента)
        debt_students = await db.execute(
            select(StudentBalance).where(StudentBalance.balance < 0)
        )
        debts = debt_students.scalars().all()

        if debts:
            user_ids = set()
            for b in debts:
                user_ids.add(b.student_id)
                user_ids.add(b.teacher_id)

            users_result = await db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            users_map = {u.id: u for u in users_result.scalars().all()}

            for balance in debts:
                student = users_map.get(balance.student_id)
                teacher = users_map.get(balance.teacher_id)

                if not student or not student.email or not teacher:
                    continue

                if await _was_sent(db, student.id, "payment", student.id):
                    continue

                await send_payment_reminder_email(
                    to_email=student.email,
                    student_name=student.full_name,
                    debt_amount=float(abs(balance.balance)),
                    teacher_name=teacher.full_name,
                )

                await _mark_sent(db, student.id, "payment", student.id)

        # Сохраняем все записи о напоминаниях
        await db.commit()


async def cleanup_old_reminders():
    """Удаляет старые записи о напоминаниях (старше 30 дней)."""
    async with AsyncSessionLocal() as db:
        cutoff = datetime.now(MSK) - timedelta(days=30)
        await db.execute(
            delete(SentReminder).where(SentReminder.sent_at < cutoff)
        )
        await db.commit()
        logger.info("Old sent_reminders cleaned up")


async def run_scheduler():
    """Запустить планировщик (проверка каждый час).

    Дополнительно: раз в сутки (в 3:00 МСК) чистит старые записи.
    """

    logger.info("🕐 Reminder scheduler started")
    last_cleanup_date = None

    while True:
        try:
            await check_and_send_reminders()

            # Раз в сутки — очистка старых записей
            now_msk = datetime.now(MSK)
            today = now_msk.date()
            if last_cleanup_date != today and now_msk.hour == 3:
                await cleanup_old_reminders()
                last_cleanup_date = today

        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")

        await asyncio.sleep(3600)