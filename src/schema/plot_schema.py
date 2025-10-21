from datetime import datetime

from pydantic import BaseModel, Field


class PlotBase(BaseModel):
    """Base schema for Plot data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    area: float = Field(..., gt=0, description="Area in hectares")
    location: str | None = None
    campaign_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)


class PlotCreate(PlotBase):
    """Schema for creating a new plot."""

    pass


class PlotUpdate(BaseModel):
    """Schema for updating a plot."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    area: float | None = Field(None, gt=0)
    location: str | None = None


class PlotInDB(PlotBase):
    """Schema for Plot as stored in database."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class PlotResponse(PlotInDB):
    """Schema for Plot response."""

    pass
