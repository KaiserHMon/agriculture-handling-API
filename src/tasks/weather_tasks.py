import asyncio
import logging
import threading
from typing import Any

from sqlalchemy import select

from src.core.celery_app import celery_app
from src.db.database import get_db_context
from src.models.notification_model import Notification
from src.models.plot_model import Plot
from src.models.user_model import User, UserRole
from src.utils.weather import WeatherService

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


@celery_app.task(name="src.tasks.weather_tasks.fetch_weather_alerts_task")
def fetch_weather_alerts_task() -> int:
    """Periodic background task to check weather forecasts for all plots and notify farmers if severe weather is detected."""
    logger.info("Background task started: Fetching weather alerts for all plots")

    async def run():
        async with get_db_context() as session:
            # Query an Admin user to act as the notification sender
            admin_stmt = select(User).where(User.role == UserRole.ADMIN).limit(1)
            admin_res = await session.execute(admin_stmt)
            admin = admin_res.scalar_one_or_none()

            if not admin:
                logger.warning(
                    "No Admin user found for sending notifications. Falling back to any user."
                )
                user_stmt = select(User).limit(1)
                user_res = await session.execute(user_stmt)
                admin = user_res.scalar_one_or_none()
                if not admin:
                    logger.error(
                        "No users exist in the database. Cannot send weather notifications."
                    )
                    return 0

            # Get all plots with locations
            plots_stmt = select(Plot).where(Plot.location.is_not(None))
            plots_res = await session.execute(plots_stmt)
            plots = plots_res.scalars().all()

            weather_service = WeatherService()
            notifications_sent = 0

            for plot in plots:
                try:
                    forecast = await weather_service.get_forecast(plot.location or "")
                    # Trigger alert for rainy or stormy conditions, or high precipitation
                    if (
                        forecast.get("conditions") in ["rainy", "stormy"]
                        or forecast.get("precipitation", 0) > 4.0
                    ):
                        title = f"Weather Alert: {plot.name}"
                        content = (
                            f"Severe weather warning for plot '{plot.name}'. "
                            f"Expected conditions: {forecast.get('conditions')}, "
                            f"temperature: {forecast.get('temperature')}°C, "
                            f"precipitation: {forecast.get('precipitation')}mm."
                        )

                        alert = Notification(
                            title=title,
                            content=content,
                            is_read=False,
                            user_id=plot.user_id,
                            sender_id=admin.id,
                        )
                        session.add(alert)
                        notifications_sent += 1
                        logger.info(
                            f"Generated weather alert for plot '{plot.name}' (User: {plot.user_id})"
                        )
                except Exception as e:
                    logger.error(f"Error checking weather for plot {plot.id}: {str(e)}")

            if notifications_sent > 0:
                await session.commit()
                logger.info(f"Successfully sent {notifications_sent} weather alert notifications")

            return notifications_sent

    return run_async(run())
