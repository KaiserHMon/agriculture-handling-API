from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError, NotFoundError
from models.notification_model import Notification
from repositories.notification_repository import NotificationRepository
from services.base_service import BaseService


class NotificationService(BaseService[Notification]):
    def __init__(self, db: AsyncSession):
        self.repository = NotificationRepository(db)
        super().__init__(self.repository, db)

    async def get_user_notifications(self, user_id: int) -> list[Notification]:
        """
        Get all notifications for a specific user.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_user_notifications(user_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_unread_notifications(self, user_id: int) -> list[Notification]:
        """
        Get all unread notifications for a specific user.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_unread_notifications(user_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def mark_as_read(self, notification_id: int) -> Notification:
        """
        Mark a notification as read.

        Raises:
            NotFoundError: If the notification doesn't exist
            HTTPException: For database errors
        """
        try:
            notification = await self.repository.mark_as_read(notification_id)
            if not notification:
                raise NotFoundError(f"Notification with id {notification_id} not found")
            return notification
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all notifications as read for a user.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.mark_all_as_read(user_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def delete_read_notifications(self, user_id: int) -> int:
        """
        Delete all read notifications for a user.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.delete_read_notifications(user_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def send_notification(self, user_id: int, title: str, message: str) -> Notification:
        """
        Create and send a new notification to a user.

        Raises:
            HTTPException: For database errors or invalid input
        """
        try:
            if not title.strip() or not message.strip():
                raise HTTPException(status_code=400, detail="Title and message are required")

            notification_data = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "is_read": False,
            }
            return await self.create(notification_data)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
