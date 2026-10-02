from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.payments.models import Payment, StudentBalance
from app.payments.schemas import PaymentCreate
from app.students.service import get_teacher_student_ids


class PaymentsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== ADD ====================

    async def add_payment(
        self, data: PaymentCreate, current_user: User
    ) -> dict:
        """Добавить платёж от ученика."""

        teacher_student_ids = await get_teacher_student_ids(
            self.db, current_user.id
        )

        if data.student_id not in teacher_student_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this student",
            )

        student_result = await self.db.execute(
            select(User)
            .where(User.id == data.student_id)
            .where(User.role == "student")
        )
        student = student_result.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        payment = Payment(
            student_id=data.student_id,
            teacher_id=current_user.id,
            amount=data.amount,
            note=data.note,
        )
        self.db.add(payment)

        balance_result = await self.db.execute(
            select(StudentBalance)
            .where(
                StudentBalance.student_id == data.student_id,
                StudentBalance.teacher_id == current_user.id,
            )
            .with_for_update()
        )
        balance = balance_result.scalar_one_or_none()

        if balance:
            balance.balance += data.amount
        else:
            balance = StudentBalance(
                student_id=data.student_id,
                teacher_id=current_user.id,
                balance=data.amount,
            )
            self.db.add(balance)

        await self.db.commit()

        return {
            "message": "Payment added",
            "new_balance": balance.balance,
        }

    # ==================== BALANCES (teacher) ====================

    async def get_students_balance(self, current_user: User) -> list[dict]:
        """Баланс всех учеников учителя."""

        student_ids = await get_teacher_student_ids(
            self.db, current_user.id
        )

        if not student_ids:
            return []

        result = await self.db.execute(
            select(User).where(User.id.in_(student_ids))
        )
        students = result.scalars().all()
        ids_list = [s.id for s in students]

        balance_result = await self.db.execute(
            select(StudentBalance).where(
                StudentBalance.teacher_id == current_user.id
            )
        )
        balances = {b.student_id: b for b in balance_result.scalars().all()}

        total_paid_result = await self.db.execute(
            select(Payment.student_id, func.sum(Payment.amount))
            .where(Payment.teacher_id == current_user.id)
            .where(Payment.student_id.in_(ids_list))
            .group_by(Payment.student_id)
        )
        total_paid_map = {row[0]: row[1] for row in total_paid_result.all()}

        response = []
        for student in students:
            balance_obj = balances.get(student.id)
            balance = balance_obj.balance if balance_obj else Decimal("0")

            total_paid = total_paid_map.get(student.id) or Decimal("0")

            total_debt = abs(balance) if balance < 0 else Decimal("0")

            response.append(
                {
                    "student_id": student.id,
                    "student_name": student.full_name,
                    "balance": balance,
                    "total_paid": total_paid,
                    "total_debt": total_debt,
                }
            )

        return response

    # ==================== BALANCES (student) ====================

    async def get_my_balances(self, current_user: User) -> list[dict]:
        """Для ученика: балансы по каждому учителю + платежи."""

        if current_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can view their balances",
            )

        balances_result = await self.db.execute(
            select(StudentBalance).where(
                StudentBalance.student_id == current_user.id
            )
        )
        balances = balances_result.scalars().all()

        payments_result = await self.db.execute(
            select(Payment)
            .where(Payment.student_id == current_user.id)
            .order_by(Payment.created_at.desc())
        )
        payments = payments_result.scalars().all()

        if not balances:
            return []

        teacher_ids = [b.teacher_id for b in balances]
        teachers_result = await self.db.execute(
            select(User).where(User.id.in_(teacher_ids))
        )
        teachers_map = {u.id: u for u in teachers_result.scalars().all()}

        payments_by_teacher: dict[int, list] = {}
        for p in payments:
            payments_by_teacher.setdefault(p.teacher_id, []).append(p)

        result = []
        for balance in balances:
            teacher = teachers_map.get(balance.teacher_id)
            teacher_payments = payments_by_teacher.get(balance.teacher_id, [])

            result.append(
                {
                    "teacher_id": balance.teacher_id,
                    "teacher_name": (
                        teacher.full_name if teacher else "Учитель"
                    ),
                    "balance": balance.balance,
                    "payments": [
                        {
                            "id": p.id,
                            "amount": p.amount,
                            "note": p.note,
                            "created_at": p.created_at,
                        }
                        for p in teacher_payments
                    ],
                }
            )

        return result

    # ==================== HISTORY ====================

    async def get_payment_history(
        self, student_id: int, current_user: User
    ) -> dict:
        """История платежей ученика."""

        if current_user.role == "teacher":
            result = await self.db.execute(
                select(Payment)
                .where(
                    Payment.student_id == student_id,
                    Payment.teacher_id == current_user.id,
                )
                .order_by(Payment.created_at.desc())
            )
            payments = result.scalars().all()

            balance_result = await self.db.execute(
                select(StudentBalance).where(
                    StudentBalance.student_id == student_id,
                    StudentBalance.teacher_id == current_user.id,
                )
            )
            balance = balance_result.scalar_one_or_none()

            return {
                "payments": payments,
                "balance": balance.balance if balance else Decimal("0"),
            }

        if current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        result = await self.db.execute(
            select(Payment)
            .where(Payment.student_id == current_user.id)
            .order_by(Payment.created_at.desc())
        )
        payments = result.scalars().all()

        balances_result = await self.db.execute(
            select(StudentBalance).where(
                StudentBalance.student_id == current_user.id
            )
        )
        balances = balances_result.scalars().all()
        total_balance = sum((b.balance for b in balances), Decimal("0"))

        return {
            "payments": payments,
            "balance": total_balance,
        }