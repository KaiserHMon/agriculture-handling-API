from datetime import datetime

from pydantic import BaseModel, Field


class PlotBase(BaseModel):

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    area: float = Field(..., gt=0, description="Area in hectares")
    location: str | None = None
    campaign_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)


class PlotCreate(PlotBase):
    pass


class PlotUpdate(BaseModel):

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    area: float | None = Field(None, gt=0)
    location: str | None = None


class PlotInDB(PlotBase):

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:

        from_attributes = True


class PlotResponse(PlotInDB):
    pass
