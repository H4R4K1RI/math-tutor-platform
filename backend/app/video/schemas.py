from pydantic import BaseModel


class VideoTokenResponse(BaseModel):
    """Ответ с JWT для подключения к Jitsi."""

    token: str
    domain: str
    room: str