import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger


class SSEManager:
    def __init__(self):
        # Maps user_id -> set of active asyncio.Queue
        # Using a set handles multiple devices/tabs for the same user
        self.active_connections: dict[int, set[asyncio.Queue]] = defaultdict(set)

    async def subscribe(self, user_id: int) -> AsyncGenerator[str, None]:
        """
        Subscribe a user to SSE events.
        Creates a queue, yields events from it, and cleans up on disconnect.
        """
        queue = asyncio.Queue()
        self.active_connections[user_id].add(queue)
        logger.info(
            f"User {user_id} subscribed to SSE. Total connections for user: {len(self.active_connections[user_id])}"
        )

        try:
            while True:
                # Wait for the next message in the queue
                message = await queue.get()
                # Format as Server-Sent Event (SSE)
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            # Client disconnected, this is expected in FastAPI when connection drops
            logger.info(f"Client disconnected for user {user_id}")
        finally:
            # THIS IS CRITICAL TO AVOID MEMORY LEAKS
            self.active_connections[user_id].discard(queue)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(
                f"Cleaned up SSE connection for user {user_id}. Remaining: {len(self.active_connections.get(user_id, []))}"
            )

    async def publish(self, user_id: int, message: dict[str, Any]):
        """
        Publish a message to all active connections for a specific user.
        """
        if user_id not in self.active_connections:
            return

        message_str = json.dumps(message)
        queues = self.active_connections[user_id]

        # We iterate over a copy of the set to avoid RuntimeError if modified during iteration
        for queue in list(queues):
            await queue.put(message_str)


# Singleton instance
sse_manager = SSEManager()
