from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError, NotFoundError
from models.plot_model import Plot
from repositories.plot_repository import PlotRepository
from services.base_service import BaseService


class PlotService(BaseService[Plot]):
    def __init__(self, db: AsyncSession):
        self.repository = PlotRepository(db)
        super().__init__(self.repository, db)

    async def get_plot_with_events(self, plot_id: int) -> Plot:
        """
        Get a plot with all its events.

        Raises:
            NotFoundError: If the plot doesn't exist
            HTTPException: For database errors
        """
        try:
            plot = await self.repository.get_plot_with_events(plot_id)
            if not plot:
                raise NotFoundError(f"Plot with id {plot_id} not found")
            return plot
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_plot_with_recommendations(self, plot_id: int) -> Plot:
        """
        Get a plot with all its recommendations.

        Raises:
            NotFoundError: If the plot doesn't exist
            HTTPException: For database errors
        """
        try:
            plot = await self.repository.get_plot_with_recommendations(plot_id)
            if not plot:
                raise NotFoundError(f"Plot with id {plot_id} not found")
            return plot
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_campaign_plots(self, campaign_id: int) -> list[Plot]:
        """
        Get all plots for a specific campaign.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_campaign_plots(campaign_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_user_plots(self, user_id: int) -> list[Plot]:
        """
        Get all plots owned by a specific user.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_user_plots(user_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_plots_by_location(self, location: str) -> list[Plot]:
        """
        Get all plots in a specific location.

        Raises:
            HTTPException: For database errors
        """
        try:
            # Validate location string
            if not location.strip():
                raise HTTPException(status_code=400, detail="Location cannot be empty")
            return await self.repository.get_plots_by_location(location)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def validate_plot_ownership(self, plot_id: int, user_id: int) -> bool:
        """
        Validate that a plot belongs to a specific user.

        Raises:
            NotFoundError: If the plot doesn't exist
            HTTPException: For database errors or unauthorized access
        """
        try:
            plot = await self.get(plot_id)
            if not plot:
                raise NotFoundError(f"Plot with id {plot_id} not found")
            if plot.user_id != user_id:
                raise HTTPException(status_code=403, detail="User does not own this plot")
            return True
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
