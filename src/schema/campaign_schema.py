from datetime import datetime

from pydantic import BaseModel, Field

from schema.plot_schema import PlotResponse


class CampaignBase(BaseModel):

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    user_id: int = Field(..., gt=0)


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class CampaignInDB(CampaignBase):

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:

        from_attributes = True


class CampaignResponse(CampaignInDB):

    plots: list[PlotResponse] | None = []


class CampaignStats(BaseModel):
    """Schema for Campaign statistics."""

    plot_count: int = Field(..., ge=0)
    total_area: float = Field(..., ge=0)


class CampaignDateUpdate(BaseModel):

    start_date: datetime | None = None
    end_date: datetime | None = None


class CampaignWithStats(CampaignResponse):
    """Schema for Campaign with statistics."""

    stats: CampaignStats
