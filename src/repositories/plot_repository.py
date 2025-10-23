from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from exceptions.api_exceptions import DatabaseError
from models.plot_model import Plot
from repositories.base_repository import BaseRepository


class PlotRepository(BaseRepository[Plot]):
    def __init__(self, db: AsyncSession):
        super().__init__(Plot, db)

    async def get_plot_with_events(self, plot_id: int) -> Plot | None:
        """Get plot with all its events."""
        try:
            query = (
                select(self.model)
                .where(self.model.id == plot_id)
                .options(joinedload(self.model.events))
            )
            result = await self.db.execute(query)
            return result.unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting plot with events for id {plot_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get plot with events",
                details={"plot_id": plot_id, "error": str(e)},
            ) from e

    async def get_plot_with_recommendations(self, plot_id: int) -> Plot | None:
        """Get plot with all its recommendations."""
        try:
            query = (
                select(self.model)
                .where(self.model.id == plot_id)
                .options(joinedload(self.model.recommendations))
            )
            result = await self.db.execute(query)
            return result.unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting plot with recommendations for id {plot_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get plot with recommendations",
                details={"plot_id": plot_id, "error": str(e)},
            ) from e

    async def get_campaign_plots(self, campaign_id: int) -> list[Plot]:
        """Get all plots for a specific campaign."""
        try:
            query = select(self.model).where(self.model.campaign_id == campaign_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting plots for campaign {campaign_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get campaign plots",
                details={"campaign_id": campaign_id, "error": str(e)},
            ) from e

    async def get_user_plots(self, user_id: int) -> list[Plot]:
        """Get all plots owned by a specific user."""
        try:
            query = select(self.model).where(self.model.user_id == user_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting plots for user {user_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get user plots", details={"user_id": user_id, "error": str(e)}
            ) from e

    async def get_plots_by_location(self, location: str) -> list[Plot]:
        """Get all plots in a specific location."""
        try:
            query = select(self.model).where(self.model.location.ilike(f"%{location}%"))
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting plots for location {location}: {str(e)}")
            raise DatabaseError(
                message="Failed to get plots by location",
                details={"location": location, "error": str(e)},
            ) from e
