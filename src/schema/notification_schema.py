from datetime import datetime

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    user_id: int = Field(..., gt=0)
    sender_id: int = Field(..., gt=0)  # ID del usuario que envía el mensaje


class NotificationCreate(NotificationBase):

    pass


class NotificationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)
    is_read: bool | None = None


class NotificationInDB(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(NotificationInDB):
    pass


class NotificationCount(BaseModel):
    total: int = Field(..., ge=0)
    unread: int = Field(..., ge=0)
