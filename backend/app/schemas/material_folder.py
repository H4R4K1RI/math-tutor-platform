from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class MaterialFolderCreate(BaseModel):
    name: str
    description: Optional[str] = None


class MaterialFolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MaterialFolderResponse(BaseModel):
    id: int
    teacher_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    materials_count: int = 0

    model_config = ConfigDict(from_attributes=True)