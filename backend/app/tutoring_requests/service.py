from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.models import Chat
from app.chat.socket import sio
from app.tutoring_requests.models import TutoringRequest
from app.tutoring_requests.schemas import (
    TutoringRequestCreate,
    TutoringRequestUpdate,
)


class TutoringRequestsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== CREATE ====================

    async def create_request(
        self, data: TutoringRequestCreate, current_user: User
    ) -> dict:
        """Ученик отправляет заявку на обучение учителю."""

        if current_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can send tutoring requests",
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
        if chat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="You are already connected"
            )

        existing_result = await self.db.execute(
            select(TutoringRequest).where(
                TutoringRequest.teacher_id == data.teacher_id,
                TutoringRequest.student_id == current_user.id,
                TutoringRequest.status == "pending",
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Request already sent")

        new_request = TutoringRequest(
            teacher_id=data.teacher_id,
            student_id=current_user.id,
            message=data.message,
            status="pending",
        )
        self.db.add(new_request)
        await self.db.commit()
        await self.db.refresh(new_request)

        try:
            await sio.emit(
                "new_tutoring_request",
                {
                    "request_id": new_request.id,
                    "teacher_id": data.teacher_id,
                    "student_name": current_user.full_name,
                },
            )
        except Exception:
            pass

        return {
            "id": new_request.id,
            "teacher_id": new_request.teacher_id,
            "student_id": new_request.student_id,
            "student_name": current_user.full_name,
            "message": new_request.message,
            "status": new_request.status,
            "created_at": new_request.created_at,
        }

    # ==================== LIST ====================

    async def get_requests(self, current_user: User) -> list[dict]:
        """Список заявок (для учителя или ученика)."""

        if current_user.role == "teacher":
            query = select(TutoringRequest).where(
                TutoringRequest.teacher_id == current_user.id
            )
        else:
            query = select(TutoringRequest).where(
                TutoringRequest.student_id == current_user.id
            )

        query = query.order_by(TutoringRequest.created_at.desc())
        result = await self.db.execute(query)
        requests = result.scalars().all()

        if not requests:
            return []

        user_ids = set()
        for req in requests:
            user_ids.add(req.student_id)
            user_ids.add(req.teacher_id)

        users_result = await self.db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users_map = {u.id: u for u in users_result.scalars().all()}

        response = []
        for req in requests:
            student = users_map.get(req.student_id)
            teacher = users_map.get(req.teacher_id)

            response.append(
                {
                    "id": req.id,
                    "teacher_id": req.teacher_id,
                    "student_id": req.student_id,
                    "student_name": (
                        student.full_name if student else "Unknown"
                    ),
                    "teacher_name": (
                        teacher.full_name if teacher else "Unknown"
                    ),
                    "message": req.message,
                    "status": req.status,
                    "created_at": req.created_at,
                }
            )

        return response

    # ==================== CHECK ====================

    async def check_connection_status(
        self, teacher_id: int, current_user: User
    ) -> dict:
        """Проверить статус связи ученика с учителем."""

        if current_user.role != "student":
            return {"is_connected": False, "has_pending_request": False}

        chat_result = await self.db.execute(
            select(Chat).where(
                Chat.teacher_id == teacher_id,
                Chat.student_id == current_user.id,
            )
        )
        chat = chat_result.scalar_one_or_none()

        req_result = await self.db.execute(
            select(TutoringRequest).where(
                TutoringRequest.teacher_id == teacher_id,
                TutoringRequest.student_id == current_user.id,
                TutoringRequest.status == "pending",
            )
        )
        pending = req_result.scalar_one_or_none()

        return {
            "is_connected": chat is not None,
            "chat_id": chat.id if chat else None,
            "has_pending_request": pending is not None,
        }

    # ==================== UPDATE ====================

    async def update_request(
        self,
        request_id: int,
        data: TutoringRequestUpdate,
        current_user: User,
    ) -> dict:
        """Принять или отклонить заявку (только учитель)."""

        result = await self.db.execute(
            select(TutoringRequest).where(
                TutoringRequest.id == request_id,
                TutoringRequest.teacher_id == current_user.id,
            )
        )
        tutoring_request = result.scalar_one_or_none()

        if not tutoring_request:
            raise HTTPException(status_code=404, detail="Request not found")

        if tutoring_request.status != "pending":
            raise HTTPException(
                status_code=400, detail="Request already processed"
            )

        tutoring_request.status = data.status

        if data.status == "approved":
            chat_result = await self.db.execute(
                select(Chat).where(
                    Chat.teacher_id == current_user.id,
                    Chat.student_id == tutoring_request.student_id,
                )
            )
            chat = chat_result.scalar_one_or_none()

            if not chat:
                chat = Chat(
                    teacher_id=current_user.id,
                    student_id=tutoring_request.student_id,
                    assignment_id=None,
                )
                self.db.add(chat)

            await self.db.commit()

            try:
                await sio.emit(
                    "tutoring_request_approved",
                    {
                        "request_id": request_id,
                        "student_id": tutoring_request.student_id,
                    },
                )
            except Exception:
                pass
        else:
            await self.db.commit()

        return {"message": f"Request {data.status}"}