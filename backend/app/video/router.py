from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.shared.db import get_db
from app.video.schemas import VideoTokenResponse
from app.video.service import VideosService

router = APIRouter(prefix="/video", tags=["video"])


@router.post(
    "/token/{lesson_id}",
    response_model=VideoTokenResponse,
)
async def get_video_token(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить JWT для Jitsi-комнаты урока."""
    service = VideosService(db)
    return await service.generate_token(lesson_id, current_user)