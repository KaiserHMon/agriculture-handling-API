from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_campaigns: int
    active_campaigns: int
    total_plots: int
    total_area: float
    total_events: int
    total_recommendations: int
