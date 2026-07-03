from celery import Celery

from src.core.config import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "agriculture_handling",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Configure Celery
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Auto-discover tasks in src.tasks
celery_app.autodiscover_tasks(["src"])
