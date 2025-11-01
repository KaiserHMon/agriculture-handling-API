from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.campaign_service import CampaignService

from ...core.auth import get_current_active_user
from ...db.database import get_db
from ...exceptions.api_exceptions import DatabaseError, NotFoundError
from ...models.user_model import User, UserRole
from ...schema.campaign_schema import (
    CampaignCreate,
    CampaignDateUpdate,
    CampaignInDB,
    CampaignResponse,
    CampaignStats,
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("/", response_model=CampaignInDB, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new campaign. Farmers can only create campaigns for themselves."""
    # Farmers can only create campaigns for themselves
    if current_user.role == UserRole.FARMER and payload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers can only create campaigns for themselves",
        )

    # Advisors can't create campaigns for others
    if current_user.role == UserRole.ADVISOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advisors cannot create campaigns",
        )

    # Admin can create for anyone, and farmers for themselves only
    if current_user.role != UserRole.ADMIN and current_user.id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create campaign for other users",
        )

    service = CampaignService(db)
    try:
        return await service.create(payload.dict())
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=list[CampaignInDB])
async def list_campaigns(
    current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """Get all campaigns. Farmers only see their own campaigns, advisors see all."""
    service = CampaignService(db)
    try:
        if current_user.role == UserRole.FARMER:
            # Farmers see only their campaigns
            return await service.get_user_campaigns(current_user.id)
        elif current_user.role == UserRole.ADVISOR:
            # Advisors can only see campaigns where they give recommendations
            # This would need a new service method - for now they see none
            return []
        else:
            # Admin sees all campaigns
            return await service.get_all()
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a campaign by id. Farmers can only view their own campaigns."""
    service = CampaignService(db)
    try:
        campaign = await service.get(campaign_id)
        if current_user.role == UserRole.FARMER:
            # Farmers can only see their own campaigns
            if campaign.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to access this campaign",
                )
        elif current_user.role == UserRole.ADVISOR:
            # Advisors can only see campaigns where they give recommendations
            # This would need a check against recommendations - for now no access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors can only access campaigns through recommendations",
            )
        # Admin has full access
        return campaign
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{campaign_id}/plots", response_model=CampaignResponse)
async def get_campaign_with_plots(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a campaign with all its plots. Farmers can only view their own campaigns."""
    service = CampaignService(db)
    try:
        campaign = await service.get_campaign_with_plots(campaign_id)
        if current_user.role == UserRole.FARMER and campaign.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this campaign",
            )
        return campaign
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/active", response_model=list[CampaignInDB])
async def get_active_campaigns(
    current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """Get all active campaigns (not ended). Farmers only see their own."""
    service = CampaignService(db)
    try:
        campaigns = await service.get_active_campaigns()
        if current_user.role == UserRole.FARMER:
            # Farmers see only their active campaigns
            return [c for c in campaigns if c.user_id == current_user.id]
        elif current_user.role == UserRole.ADVISOR:
            # Advisors can only see campaigns where they give recommendations
            # Would need a recommendations check - for now return none
            return []
        # Admin sees all active campaigns
        return campaigns
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/user/{user_id}", response_model=list[CampaignInDB])
async def get_user_campaigns(user_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    """Get all campaigns for a specific user."""
    service = CampaignService(db)
    try:
        return await service.get_user_campaigns(user_id)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get statistics for a campaign. Farmers can only view their own campaigns' stats."""
    service = CampaignService(db)
    try:
        # First check if user can access this campaign
        campaign = await service.get(campaign_id)
        if current_user.role == UserRole.FARMER and campaign.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this campaign's statistics",
            )
        return await service.get_campaign_stats(campaign_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{campaign_id}/dates", response_model=CampaignResponse)
async def update_campaign_dates(
    campaign_id: int,
    payload: CampaignDateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update a campaign's start and/or end dates. Farmers can only update their own campaigns."""
    service = CampaignService(db)
    try:
        # First check if user can access this campaign
        campaign = await service.get(campaign_id)
        if current_user.role == UserRole.FARMER:
            if campaign.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to update this campaign",
                )
        elif current_user.role == UserRole.ADVISOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors cannot modify campaigns",
            )
        return await service.update_campaign_dates(
            campaign_id, payload.start_date, payload.end_date
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/range", response_model=list[CampaignInDB])
async def get_campaigns_by_date_range(
    start_date: datetime,
    end_date: datetime,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get campaigns that start within a date range. Farmers only see their own campaigns."""
    service = CampaignService(db)
    try:
        campaigns = await service.get_campaigns_by_date_range(start_date, end_date)
        if current_user.role == UserRole.FARMER:
            # Filter campaigns for farmer
            return [c for c in campaigns if c.user_id == current_user.id]
        return campaigns
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{campaign_id}/close", response_model=CampaignResponse)
async def close_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Close a campaign by setting its end date to now. Farmers can only close their own campaigns."""
    service = CampaignService(db)
    try:
        # First check if user can access this campaign
        campaign = await service.get(campaign_id)
        if current_user.role == UserRole.FARMER and campaign.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to close this campaign",
            )
        return await service.close_campaign(campaign_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/recent", response_model=list[CampaignInDB])
async def get_recent_campaigns(
    limit: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get most recent campaigns (by start_date), limit default 5. Farmers only see their own campaigns."""
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be greater than 0")
    service = CampaignService(db)
    try:
        if current_user.role == UserRole.FARMER:
            # For farmers, get their campaigns and sort/limit in memory
            user_campaigns = await service.get_user_campaigns(current_user.id)
            sorted_campaigns = sorted(user_campaigns, key=lambda c: c.start_date, reverse=True)
            return sorted_campaigns[:limit]
        return await service.get_recent_campaigns(limit)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
