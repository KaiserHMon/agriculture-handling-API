import logging

logger = logging.getLogger(__name__)


class WeatherService:

    async def get_forecast(self, location: str) -> dict:
        """Fetch weather forecast for a given location."""
        logger.info(f"Fetching weather forecast for location: {location}")
        # Return a default mock structure
        return {
            "temperature": 22.5,
            "precipitation": 5.0,
            "conditions": "rainy",
        }
