from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions.api_exceptions import DatabaseError
from ..repositories.metric_repository import MetricRepository
from ..schema.metric_schema import DashboardMetrics


class MetricService:
    def __init__(self, db: AsyncSession):
        self.repository = MetricRepository(db)

    async def get_dashboard_metrics(
        self, user_id: int | None = None, role: str | None = None
    ) -> DashboardMetrics:
        try:
            metrics_dict = await self.repository.get_dashboard_metrics(user_id, role)
            return DashboardMetrics(**metrics_dict)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
