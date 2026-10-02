from pydantic import BaseModel
from typing import Optional


class MessageCreate(BaseModel):
    chat_id: int
    message: str


class ChatCreate(BaseModel):
    student_id: int
    assignment_id: Optional[int] = None