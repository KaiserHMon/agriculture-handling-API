from datetime import datetime

from loguru import logger
from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.campaign_model import Campaign
from models.plot_model import Plot
from repositories.base_repository import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):

    def __init__(self, db: AsyncSession):
        super().__init__(Campaign, db)

    async def get_campaign_with_plots(self, campaign_id: int) -> Campaign | None:
        """Get campaign with all its plots."""
        try:
            query = (
                select(self.model)
                .where(self.model.id == campaign_id)
                .options(joinedload(self.model.plots))
            )
            result = await self.db.execute(query)
            return result.unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting campaign with plots for id {campaign_id}: {str(e)}")
            raise

    async def get_active_campaigns(self) -> list[Campaign]:
        """Get all active campaigns (not ended)."""
        try:
            query = select(self.model).where(
                and_(self.model.end_date.is_(None), self.model.start_date <= datetime.utcnow())
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError:
            logger.error("Error getting active campaigns: {str(e)}")
            raise

    async def get_user_campaigns(self, user_id: int) -> list[Campaign]:
        """Get all campaigns for a specific user."""
        try:
            query = (
                select(self.model)
                .where(self.model.user_id == user_id)
                .order_by(self.model.start_date.desc())
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting campaigns for user {user_id}: {str(e)}")
            raise

    async def get_campaign_stats(self, campaign_id: int) -> dict:
        """Get campaign statistics."""
        try:
            # Get total area and plot count
            area_query = select(
                func.count(Plot.id).label("plot_count"), func.sum(Plot.area).label("total_area")
            ).where(Plot.campaign_id == campaign_id)

            result = await self.db.execute(area_query)
            stats = result.mappings().one()

            return {
                "plot_count": int(stats["plot_count"]),
                "total_area": float(stats["total_area"] or 0),
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting stats for campaign {campaign_id}: {str(e)}")
            raise

    async def update_campaign_dates(
        self, campaign_id: int, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> Campaign | None:
        """Update campaign dates."""
        try:
            campaign = await self.get(campaign_id)
            if not campaign:
                return None

            if start_date:
                campaign.start_date = start_date
            if end_date:
                campaign.end_date = end_date

            await self.db.commit()
            await self.db.refresh(campaign)
            return campaign
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating dates for campaign {campaign_id}: {str(e)}")
            raise

    async def get_campaigns_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[Campaign]:
        """Get campaigns within a date range."""
        try:
            query = (
                select(self.model)
                .where(and_(self.model.start_date >= start_date, self.model.start_date <= end_date))
                .order_by(self.model.start_date)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting campaigns between {start_date} and {end_date}: {str(e)}")
            raise

    async def close_campaign(self, campaign_id: int) -> Campaign | None:
        """Close a campaign by setting its end date."""
        try:
            campaign = await self.get(campaign_id)
            if not campaign:
                return None

            campaign.end_date = datetime.now()
            await self.db.commit()
            await self.db.refresh(campaign)
            return campaign
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error closing campaign {campaign_id}: {str(e)}")
            raise

    async def get_recent_campaigns(self, limit: int = 5) -> list[Campaign]:
        """Get most recent campaigns."""
        try:
            query = select(self.model).order_by(self.model.start_date.desc()).limit(limit)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent campaigns: {str(e)}")
            raise
