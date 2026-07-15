from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_active_user
from ...db.database import get_db
from ...models.user_model import User
from ...schema.metric_schema import DashboardMetrics
from ...services.metric_service import MetricService

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated dashboard metrics for the current user."""
    service = MetricService(db)
    return await service.get_dashboard_metrics(
        user_id=current_user.id, role=current_user.role.value
    )
