from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError, NotFoundError
from models.event_model import Event
from repositories.event_repository import EventRepository
from services.base_service import BaseService


class EventService(BaseService[Event]):
    def __init__(self, db: AsyncSession):
        self.repository = EventRepository(db)
        super().__init__(self.repository, db)

    async def get_plot_events(self, plot_id: int) -> list[Event]:
        """
        Get all events for a specific plot.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_plot_events(plot_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_campaign_events(self, campaign_id: int) -> list[Event]:
        """
        Get all events for a specific campaign.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_campaign_events(campaign_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_user_events(self, user_id: int) -> list[Event]:
        """
        Get all events created by a specific user.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_user_created_events(user_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_events_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[Event]:
        """
        Get all events within a date range.

        Raises:
            HTTPException: For database errors or invalid date range
        """
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="End date must be after start date",
            )

        try:
            return await self.repository.get_events_by_date_range(start_date, end_date)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_upcoming_events(self, days: int = 7) -> list[Event]:
        """
        Get upcoming events within the next X days.

        Args:
            days: Number of days to look ahead (default: 7)

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_upcoming_events(days)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def validate_event_ownership(
        self, event_id: int, user_id: int, allow_admin: bool = True
    ) -> Event:
        """
        Validate that an event was created by a specific user.

        Args:
            event_id: ID of the event to validate
            user_id: ID of the user to check
            allow_admin: If True, admins can access any event

        Raises:
            NotFoundError: If the event doesn't exist
            HTTPException: For database errors or unauthorized access
        """
        try:
            event = await self.get(event_id)
            if not event:
                raise NotFoundError(f"Event with id {event_id} not found")

            if event.created_by_id != user_id and not allow_admin:
                raise HTTPException(status_code=403, detail="User does not own this event")

            return event
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
