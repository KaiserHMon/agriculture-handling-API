import asyncio
import logging
import threading
from typing import Any

from src.core.celery_app import celery_app
from src.utils.calendar import GoogleCalendarClient

logger = logging.getLogger(__name__)


def run_async(coro) -> Any:
    """Run an async coroutine in a separate thread to prevent deadlocks in synchronous contexts."""
    result = None
    exception = None

    def worker():
        nonlocal result, exception
        try:
            result = asyncio.run(coro)
        except Exception as e:
            exception = e

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result


@celery_app.task(name="src.tasks.calendar_tasks.sync_event_task")
def sync_event_task(event_id: int, title: str, start_time: str) -> bool:
    """Celery background task to synchronize an event to Google Calendar."""
    logger.info(f"Background task started: Syncing event {event_id} ({title}) to Google Calendar")

    from datetime import datetime

    dt = None
    if start_time:
        try:
            dt_str = start_time.replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
        except Exception as e:
            logger.error(f"Failed to parse start_time '{start_time}': {e}")

    client = GoogleCalendarClient()
    return run_async(client.sync_event(event_id=event_id, title=title, start_time=dt))
