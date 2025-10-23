from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError
from models.notification_model import Notification
from repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)

    async def get_user_notifications(self, user_id: int) -> list[Notification]:
        """Get all notifications for a specific user."""
        try:
            query = select(self.model).where(self.model.user_id == user_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get user notifications",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def get_unread_notifications(self, user_id: int) -> list[Notification]:
        """Get all unread notifications for a specific user."""
        try:
            query = select(self.model).where(self.model.user_id == user_id, ~self.model.is_read)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting unread notifications for user {user_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get unread notifications",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def mark_as_read(self, notification_id: int) -> Notification | None:
        """Mark a notification as read."""
        try:
            notification = await self.get(notification_id)
            if not notification:
                return None

            notification.is_read = True
            await self.db.commit()
            await self.db.refresh(notification)
            return notification
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            raise DatabaseError(
                message="Failed to mark notification as read",
                details={"notification_id": notification_id, "error": str(e)},
            ) from e

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        try:
            query = select(self.model).where(self.model.user_id == user_id, ~self.model.is_read)
            result = await self.db.execute(query)
            notifications = list(result.scalars().all())

            count = 0
            for notification in notifications:
                notification.is_read = True
                count += 1

            await self.db.commit()
            return count
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to mark all notifications as read",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def delete_read_notifications(self, user_id: int) -> int:
        """Delete all read notifications for a user."""
        try:
            query = select(self.model).where(self.model.user_id == user_id, self.model.is_read)
            result = await self.db.execute(query)
            notifications = list(result.scalars().all())

            count = 0
            for notification in notifications:
                await self.db.delete(notification)
                count += 1

            await self.db.commit()
            return count
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting read notifications for user {user_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to delete read notifications",
                details={"user_id": user_id, "error": str(e)},
            ) from e
