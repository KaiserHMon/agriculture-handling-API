# ADR 0004: Real-time Notifications using Server-Sent Events (SSE)

## Status
Accepted

## Context
Our application requires a mechanism to push real-time notifications to farmers. Specifically, we want farmers to be notified immediately when:
1. An advisor creates a new technical recommendation for one of their plots.
2. An event (e.g. sowing, fertilizing) is updated by someone other than the plot owner (like an administrator).

We evaluated three potential communication patterns for this requirement:
1. **Short Polling**: Simple to implement but introduces high server overhead, database strain, and latency.
2. **WebSockets**: Bi-directional, stateful communication. However, it introduces high protocol complexity, requires dedicated connection handling, lacks native automatic reconnection, and is unnecessary because notification streaming is strictly unidirectional (server-to-client).
3. **Server-Sent Events (SSE)**: Unidirectional, real-time push over standard HTTP. It is natively supported by modern browsers (via `EventSource`), automatically handles reconnection, and integrates seamlessly with FastAPI's `StreamingResponse`.

## Decision
We enforce the use of **Server-Sent Events (SSE)** for unidirectional real-time updates:

1. **SSE Manager Class**: We introduced a singleton `SSEManager` in [sse.py](file:///C:/Proyectos/Api-AgricultureHandling/src/core/sse.py) to manage subscriber queues.
   - It maps `user_id` to a `set[asyncio.Queue]` to support multiple concurrent devices/tabs for a single user.
   - It implements a `subscribe` method that yields formatted SSE payloads (`data: <json>\n\n`) and cleans up after client disconnection to avoid memory leaks.
   - It implements a `publish` method to enqueue messages for all active connections of a specific user.
2. **API Endpoint**: We exposed a protected endpoint `GET /api/v1/notifications/sse` in [notification_api.py](file:///C:/Proyectos/Api-AgricultureHandling/src/api/v1/notification_api.py).
   - This endpoint uses FastAPI's `StreamingResponse` wrapping `sse_manager.subscribe(current_user.id)`.
   - Requires Auth0 Bearer authentication, aligning with our security policy.
3. **Integration Points**:
   - In [recommendation_api.py](file:///C:/Proyectos/Api-AgricultureHandling/src/api/v1/recommendation_api.py), when a new recommendation is successfully created, we publish an event to the owner of the plot.
   - In [event_api.py](file:///C:/Proyectos/Api-AgricultureHandling/src/api/v1/event_api.py), when an event is updated by a user other than the plot owner (e.g., an administrator), we publish an event to the owner of the plot.

## Consequences

### Positive
* **Simplicity**: No custom socket handshake or frame decoding. Operates over standard HTTP.
* **Resilience**: Browsers automatically reconnect when the connection drops, with customizable retry intervals.
* **Low resource overhead**: Uses standard asynchronous FastAPI and `asyncio.Queue` structures, taking advantage of standard event loops.
* **Memory leak prevention**: Clear `try...finally` block guarantees that closed/disconnected queues are removed from the connection dictionary.

### Negative
* **Unidirectional**: Clients cannot send messages to the server over the SSE stream. However, standard HTTP POST/PUT endpoints are sufficient for client-to-server operations.
* **HTTP/1.1 Connection limits**: Traditional browsers limit active connections to 6 per domain on HTTP/1.1. In production, this must be mitigated by serving the API over HTTP/2 or HTTP/3, which allows multiplexed connections.
