from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.board.models import Board
from app.lessons.models import Lesson


class BoardsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_lesson_for_user(
        self, lesson_id: int, current_user: User
    ) -> Lesson:
        """Проверить, что пользователь имеет доступ к уроку.

        Доступ: учитель урока или ученик урока.
        """
        result = await self.db.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        if current_user.id not in (lesson.teacher_id, lesson.student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return lesson

    async def get_or_create(
        self, lesson_id: int, current_user: User
    ) -> Board:
        """Получить доску урока. Создаёт пустую, если её нет."""
        await self._get_lesson_for_user(lesson_id, current_user)

        result = await self.db.execute(
            select(Board).where(Board.lesson_id == lesson_id)
        )
        board = result.scalar_one_or_none()

        if not board:
            board = Board(lesson_id=lesson_id, state={})
            self.db.add(board)
            await self.db.commit()
            await self.db.refresh(board)

        return board

    async def update(
        self,
        lesson_id: int,
        state: Dict[str, Any],
        current_user: User,
    ) -> Board:
        """Обновить состояние доски."""
        board = await self.get_or_create(lesson_id, current_user)

        board.state = state
        await self.db.commit()
        await self.db.refresh(board)

        return board

    async def clear(
        self, lesson_id: int, current_user: User
    ) -> Board:
        """Очистить доску (установить пустое состояние)."""
        return await self.update(lesson_id, {}, current_user)