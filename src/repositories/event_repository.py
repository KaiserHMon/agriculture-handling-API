from datetime import datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError
from models.event_model import Event
from repositories.base_repository import BaseRepository


class EventRepository(BaseRepository[Event]):
    def __init__(self, db: AsyncSession):
        super().__init__(Event, db)

    async def get_plot_events(self, plot_id: int) -> list[Event]:
        """Get all events for a specific plot."""
        try:
            query = select(self.model).where(self.model.plot_id == plot_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting events for plot {plot_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get plot events", details={"plot_id": plot_id, "error": str(e)}
            ) from e

    async def get_campaign_events(self, campaign_id: int) -> list[Event]:
        """Get all events for a specific campaign."""
        try:
            query = select(self.model).where(self.model.campaign_id == campaign_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting events for campaign {campaign_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get campaign events",
                details={"campaign_id": campaign_id, "error": str(e)},
            ) from e

    async def get_user_created_events(self, user_id: int) -> list[Event]:
        """Get all events created by a specific user."""
        try:
            query = select(self.model).where(self.model.created_by_id == user_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting events created by user {user_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get user created events",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def get_events_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[Event]:
        """Get all events within a date range."""
        try:
            query = (
                select(self.model)
                .where(self.model.event_date >= start_date, self.model.event_date <= end_date)
                .order_by(self.model.event_date)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting events between {start_date} and {end_date}: {str(e)}")
            raise

    async def get_upcoming_events(self, days: int = 7) -> list[Event]:
        """Get upcoming events within the next X days."""
        try:
            now = datetime.now()
            future = datetime.now() + timedelta(days=days)
            query = (
                select(self.model)
                .where(self.model.event_date >= now, self.model.event_date <= future)
                .order_by(self.model.event_date)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            raise
