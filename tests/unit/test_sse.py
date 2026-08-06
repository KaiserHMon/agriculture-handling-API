import asyncio

import pytest

from src.core.sse import SSEManager


@pytest.mark.anyio
async def test_sse_subscribe_and_publish():
    # 1. Initialize manager
    manager = SSEManager()
    user_id = 42

    # 2. Check empty connections
    assert user_id not in manager.active_connections

    # 3. Create subscription generator
    gen = manager.subscribe(user_id)

    # 4. Start generator in a background task so it can await messages
    # We use anext() (or __anext__()) to drive the generator
    async def run_gen():
        try:
            return await gen.__anext__()
        except GeneratorExit:
            raise
        except Exception as e:
            return e

    task = asyncio.create_task(run_gen())

    # Yield control to let the generator execute up to the queue.get() await
    await asyncio.sleep(0.05)

    # Verify connection was registered
    assert user_id in manager.active_connections
    assert len(manager.active_connections[user_id]) == 1

    # 5. Publish message
    message = {"type": "test_event", "data": "hello"}
    await manager.publish(user_id, message)

    # 6. Check received value
    result = await task
    assert result == 'data: {"type": "test_event", "data": "hello"}\n\n'

    # 7. Clean up subscription
    await gen.aclose()
    await asyncio.sleep(0.05)

    # Verify connection was cleaned up and dictionary key deleted
    assert user_id not in manager.active_connections


@pytest.mark.anyio
async def test_sse_multiple_connections_same_user():
    manager = SSEManager()
    user_id = 100

    # Create two subscriptions
    gen1 = manager.subscribe(user_id)
    gen2 = manager.subscribe(user_id)

    async def get_next(gen):
        return await gen.__anext__()

    task1 = asyncio.create_task(get_next(gen1))
    task2 = asyncio.create_task(get_next(gen2))

    await asyncio.sleep(0.05)

    # Both should be in active_connections
    assert user_id in manager.active_connections
    assert len(manager.active_connections[user_id]) == 2

    # Publish
    await manager.publish(user_id, {"val": "multi"})

    res1 = await task1
    res2 = await task2

    assert res1 == 'data: {"val": "multi"}\n\n'
    assert res2 == 'data: {"val": "multi"}\n\n'

    # Close one subscription
    await gen1.aclose()
    await asyncio.sleep(0.05)

    # Should still have one connection active
    assert user_id in manager.active_connections
    assert len(manager.active_connections[user_id]) == 1

    # Close the second subscription
    await gen2.aclose()
    await asyncio.sleep(0.05)

    # Should be fully cleaned up
    assert user_id not in manager.active_connections


@pytest.mark.anyio
async def test_sse_publish_no_connections():
    manager = SSEManager()
    # Publishing to a non-existent user should do nothing and not raise errors
    await manager.publish(999, {"msg": "silent"})
    assert 999 not in manager.active_connections
