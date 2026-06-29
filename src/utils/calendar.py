import logging

logger = logging.getLogger(__name__)


class GoogleCalendarClient:

    async def sync_event(self, event_id: int, title: str, start_time) -> bool:
        """Syncs an agricultural event with Google Calendar."""
        logger.info(f"Syncing event {event_id} ({title}) to Google Calendar at {start_time}")
        return True
