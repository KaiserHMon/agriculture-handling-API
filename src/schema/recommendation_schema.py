from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationBase(BaseModel):

    content: str = Field(..., min_length=1)
    plot_id: int = Field(..., gt=0)
    advisor_id: int = Field(..., gt=0)


class RecommendationCreate(RecommendationBase):

    pass


class RecommendationUpdate(BaseModel):
    content: str | None = Field(None, min_length=1)


class RecommendationInDB(RecommendationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class RecommendationResponse(RecommendationInDB):

    pass


class RecommendationWithPlot(RecommendationResponse):
    """Schema for Recommendation with Plot details."""

    from schema.plot_schema import PlotResponse

    plot: PlotResponse
