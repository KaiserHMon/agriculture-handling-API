from datetime import datetime

from loguru import logger
from sqlalchemy import and_, false, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions.api_exceptions import DatabaseError
from ..models.campaign_model import Campaign
from ..models.event_model import Event
from ..models.plot_model import Plot
from ..models.recommendation_model import Recommendation


class MetricRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_metrics(
        self, user_id: int | None = None, role: str | None = None
    ) -> dict:
        try:
            cq = select(func.count(Campaign.id))
            acq = select(func.count(Campaign.id)).where(
                and_(Campaign.end_date.is_(None), Campaign.start_date <= datetime.utcnow())
            )
            pq = select(func.count(Plot.id))
            aq = select(func.sum(Plot.area))
            eq = select(func.count(Event.id))
            rq = select(func.count(Recommendation.id))

            if role and user_id:
                if role == "farmer":
                    cq = cq.where(Campaign.user_id == user_id)
                    acq = acq.where(Campaign.user_id == user_id)
                    pq = pq.where(Plot.user_id == user_id)
                    aq = aq.where(Plot.user_id == user_id)
                    eq = eq.where(Event.created_by_id == user_id)
                    rq = rq.join(Plot, Recommendation.plot_id == Plot.id).where(
                        Plot.user_id == user_id
                    )
                elif role == "advisor":
                    cq = cq.where(false())
                    acq = acq.where(false())
                    pq = pq.where(false())
                    aq = aq.where(false())
                    eq = eq.where(Event.created_by_id == user_id)
                    rq = rq.where(Recommendation.advisor_id == user_id)

            total_campaigns = await self.db.scalar(cq) or 0
            active_campaigns = await self.db.scalar(acq) or 0
            total_plots = await self.db.scalar(pq) or 0
            total_area = await self.db.scalar(aq) or 0.0
            total_events = await self.db.scalar(eq) or 0
            total_recommendations = await self.db.scalar(rq) or 0

            return {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "total_plots": total_plots,
                "total_area": float(total_area),
                "total_events": total_events,
                "total_recommendations": total_recommendations,
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            raise DatabaseError(
                message="Failed to get dashboard metrics", details={"error": str(e)}
            ) from e
