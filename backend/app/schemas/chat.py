from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    message: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: int
    other_user_id: int
    other_user_name: str
    assignment_id: Optional[int] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    chat_id: int
    message: str

class ChatCreate(BaseModel):
    student_id: int
    assignment_id: Optional[int] = None
