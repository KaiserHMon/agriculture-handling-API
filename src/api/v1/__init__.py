from fastapi import APIRouter

from .auth_api import router as auth_router
from .campaign_api import router as campaign_router
from .event_api import router as event_router
from .metric_api import router as metric_router
from .notification_api import router as notification_router
from .plot_api import router as plot_router
from .recommendation_api import router as recommendation_router
from .user_api import router as user_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(campaign_router)
v1_router.include_router(event_router)
v1_router.include_router(metric_router)
v1_router.include_router(notification_router)
v1_router.include_router(plot_router)
v1_router.include_router(recommendation_router)
v1_router.include_router(user_router)
