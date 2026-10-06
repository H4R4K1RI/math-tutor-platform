from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class BoardState(BaseModel):
    """Состояние доски — произвольный JSON от tldraw."""

    state: Dict[str, Any]


class BoardUpdate(BaseModel):
    """Обновление состояния доски."""

    state: Dict[str, Any]


class BoardResponse(BaseModel):
    """Ответ с состоянием доски."""

    lesson_id: int
    state: Dict[str, Any]
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)