from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from exceptions.api_exceptions import DatabaseError
from models.recommendation_model import Recommendation
from repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Recommendation, db)

    async def get_plot_recommendations(self, plot_id: int) -> list[Recommendation]:
        """Get all recommendations for a specific plot."""
        try:
            query = select(self.model).where(self.model.plot_id == plot_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting recommendations for plot {plot_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get plot recommendations",
                details={"plot_id": plot_id, "error": str(e)},
            ) from e

    async def get_advisor_recommendations(self, advisor_id: int) -> list[Recommendation]:
        """Get all recommendations made by a specific advisor."""
        try:
            query = select(self.model).where(self.model.advisor_id == advisor_id)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting recommendations by advisor {advisor_id}: {str(e)}")
            raise DatabaseError(
                message="Failed to get advisor recommendations",
                details={"advisor_id": advisor_id, "error": str(e)},
            ) from e

    async def get_recommendation_with_plot(self, recommendation_id: int) -> Recommendation | None:
        """Get recommendation with plot details."""
        try:
            query = (
                select(self.model)
                .where(self.model.id == recommendation_id)
                .options(joinedload(self.model.plot))
            )
            result = await self.db.execute(query)
            return result.unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting recommendation with plot for id {recommendation_id}: {str(e)}"
            )
            raise DatabaseError(
                message="Failed to get recommendation with plot",
                details={"recommendation_id": recommendation_id, "error": str(e)},
            ) from e
