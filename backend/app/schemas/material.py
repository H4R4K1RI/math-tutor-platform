from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class MaterialCreate(BaseModel):
    folder_id: int
    title: str
    description: Optional[str] = None
    type: str
    url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    order: int = 0


class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class MaterialResponse(BaseModel):
    id: int
    folder_id: int
    teacher_id: int
    title: str
    description: Optional[str]
    type: str
    url: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    order: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)