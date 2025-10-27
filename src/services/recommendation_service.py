from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError, NotFoundError
from models.recommendation_model import Recommendation
from repositories.recommendation_repository import RecommendationRepository
from services.base_service import BaseService


class RecommendationService(BaseService[Recommendation]):
    def __init__(self, db: AsyncSession):
        self.repository = RecommendationRepository(db)
        super().__init__(self.repository, db)

    async def get_plot_recommendations(self, plot_id: int) -> list[Recommendation]:
        """
        Get all recommendations for a specific plot.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_plot_recommendations(plot_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_advisor_recommendations(self, advisor_id: int) -> list[Recommendation]:
        """
        Get all recommendations made by a specific advisor.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_advisor_recommendations(advisor_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_recommendation_with_plot(self, recommendation_id: int) -> Recommendation:
        """
        Get recommendation with plot details.

        Raises:
            NotFoundError: If the recommendation doesn't exist
            HTTPException: For database errors
        """
        try:
            recommendation = await self.repository.get_recommendation_with_plot(recommendation_id)
            if not recommendation:
                raise NotFoundError(f"Recommendation with id {recommendation_id} not found")
            return recommendation
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def create_recommendation(
        self, plot_id: int, advisor_id: int, content: str, priority: str
    ) -> Recommendation:
        """
        Create a new recommendation.

        Raises:
            HTTPException: For database errors or invalid input
        """
        try:
            if not content.strip():
                raise HTTPException(status_code=400, detail="Content cannot be empty")

            recommendation_data = {
                "plot_id": plot_id,
                "advisor_id": advisor_id,
                "content": content,
                "priority": priority,
                "is_implemented": False,
            }
            return await self.create(recommendation_data)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def mark_as_implemented(self, recommendation_id: int) -> Recommendation:
        """
        Mark a recommendation as implemented.

        Raises:
            NotFoundError: If the recommendation doesn't exist
            HTTPException: For database errors
        """
        try:
            recommendation = await self.get(recommendation_id)
            if not recommendation:
                raise NotFoundError(f"Recommendation with id {recommendation_id} not found")

            update_data = {"is_implemented": True}
            return await self.update(recommendation_id, update_data)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
