from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.api_exceptions import DatabaseError, NotFoundError
from models.campaign_model import Campaign
from repositories.campaign_repository import CampaignRepository
from services.base_service import BaseService


class CampaignService(BaseService[Campaign]):
    def __init__(self, db: AsyncSession):
        self.repository = CampaignRepository(db)
        super().__init__(self.repository, db)

    async def get_campaign_with_plots(self, campaign_id: int) -> Campaign:
        """
        Get a campaign with all its plots.

        Raises:
            NotFoundError: If the campaign doesn't exist
            HTTPException: For database errors
        """
        try:
            campaign = await self.repository.get_campaign_with_plots(campaign_id)
            if not campaign:
                raise NotFoundError(f"Campaign with id {campaign_id} not found")
            return campaign
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_active_campaigns(self) -> list[Campaign]:
        """
        Get all active campaigns.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_active_campaigns()
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_user_campaigns(self, user_id: int) -> list[Campaign]:
        """
        Get all campaigns for a specific user.

        Raises:
            HTTPException: For database errors
        """
        try:
            return await self.repository.get_user_campaigns(user_id)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_campaign_stats(self, campaign_id: int) -> dict[str, Any]:
        """
        Get campaign statistics.

        Raises:
            HTTPException: For database errors
        """
        try:
            stats = await self.repository.get_campaign_stats(campaign_id)
            if not stats:
                raise NotFoundError(f"Campaign with id {campaign_id} not found")
            return stats
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def update_campaign_dates(
        self, campaign_id: int, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> Campaign:
        """
        Update campaign dates.

        Raises:
            NotFoundError: If the campaign doesn't exist
            HTTPException: For database errors or invalid dates
        """
        try:
            # Validate dates
            if start_date and end_date and start_date >= end_date:
                raise HTTPException(status_code=400, detail="End date must be after start date")

            campaign = await self.repository.update_campaign_dates(
                campaign_id, start_date, end_date
            )
            if not campaign:
                raise NotFoundError(f"Campaign with id {campaign_id} not found")
            return campaign
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_campaigns_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[Campaign]:
        """
        Get campaigns within a date range.

        Raises:
            HTTPException: For database errors or invalid dates
        """
        try:
            if start_date >= end_date:
                raise HTTPException(status_code=400, detail="End date must be after start date")
            return await self.repository.get_campaigns_by_date_range(start_date, end_date)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def close_campaign(self, campaign_id: int) -> Campaign:
        """
        Close a campaign by setting its end date.

        Raises:
            NotFoundError: If the campaign doesn't exist
            HTTPException: For database errors
        """
        try:
            campaign = await self.repository.close_campaign(campaign_id)
            if not campaign:
                raise NotFoundError(f"Campaign with id {campaign_id} not found")
            return campaign
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_recent_campaigns(self, limit: int = 5) -> list[Campaign]:
        """
        Get most recent campaigns.

        Raises:
            HTTPException: For database errors or invalid limit
        """
        try:
            if limit < 1:
                raise HTTPException(status_code=400, detail="Limit must be greater than 0")
            return await self.repository.get_recent_campaigns(limit)
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
