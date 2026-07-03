# ADR 0002: Asynchronous Background Processing with Celery

## Status
Accepted

## Context
Our API is responsible for operations that integrate with third-party networks, such as syncing Google Calendar events and fetching weather recommendations. These external API calls are inherently slow, error-prone, or subject to rate limits. Performing them synchronously during an HTTP request would:
1. Block the event loop and increase client response latency.
2. Cause request failures if external services are temporarily offline.

To solve this, we need a reliable background processing system that can execute tasks asynchronously, support retry mechanisms, and decouple external dependencies from our core HTTP responses.

## Decision
We adopt **Celery** as our background task worker library, paired with **Redis** as the message broker.

1. **Task Location**: All background tasks must be located within the `src/tasks/` package and decorated with Celery's `@shared_task`.
2. **Celery Configuration**: The Celery instance is initialized in `src/core/celery_app.py` using configuration from Pydantic settings.
3. **Execution Model**:
   * **Development/Local:** Celery runs as a separate process parallel to the FastAPI server:
     ```bash
     uv run celery -A src.core.celery_app worker --loglevel=info
     ```
   * **Containerized:** Celery workers run in a dedicated container specified in the `docker-compose.yml` file, sharing the same code base and network as the API.
4. **Broker Dependency**: Redis must be running and reachable using settings from `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`.

## Consequences

### Positive
* **User Experience**: Fast HTTP responses since long-running computations and external API integrations are offloaded to background threads.
* **Resilience**: Task failures can be configured with automatic retry rules and exponential backoffs without impacting HTTP requests.
* **Scalability**: Celery workers can be scaled independently of the API container to handle large task volumes.

### Negative
* **Infrastructure Overhead**: Requires maintaining and running a Redis broker and at least one Celery worker process.
* **Debugging Complexity**: Monitoring tasks and handling failures requires checking separate logs (or installing monitoring tools like Flower).
