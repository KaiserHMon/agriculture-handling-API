from datetime import datetime

from pydantic import BaseModel, Field

from schema.plot_schema import PlotResponse


class CampaignBase(BaseModel):
    """Base schema for Campaign data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    user_id: int = Field(..., gt=0)


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""

    pass


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class CampaignInDB(CampaignBase):
    """Schema for Campaign as stored in database."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class CampaignResponse(CampaignInDB):
    """Schema for Campaign response."""

    plots: list[PlotResponse] | None = []


class CampaignStats(BaseModel):
    """Schema for Campaign statistics."""

    plot_count: int = Field(..., ge=0)
    total_area: float = Field(..., ge=0)


class CampaignDateUpdate(BaseModel):
    """Schema for updating campaign dates."""

    start_date: datetime | None = None
    end_date: datetime | None = None


class CampaignWithStats(CampaignResponse):
    """Schema for Campaign with statistics."""

    stats: CampaignStats
