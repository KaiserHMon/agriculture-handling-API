from datetime import datetime

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    event_date: datetime
    plot_id: int = Field(..., gt=0)
    campaign_id: int = Field(..., gt=0)
    created_by_id: int = Field(..., gt=0)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    event_date: datetime | None = None


class EventInDB(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class EventResponse(EventInDB):
    pass


class EventDateRange(BaseModel):
    """Schema for querying events by date range."""

    start_date: datetime
    end_date: datetime = Field(..., description="Must be after start_date")
