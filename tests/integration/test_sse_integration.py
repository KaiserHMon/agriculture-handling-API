import asyncio

import pytest
from fastapi.responses import StreamingResponse
from httpx import AsyncClient
from loguru import logger

from src.api.v1.notification_api import sse_notifications
from src.core.auth import get_current_active_user
from src.core.sse import sse_manager
from src.main import app
from src.models.user_model import User


@pytest.mark.anyio
async def test_sse_endpoint_metadata_and_direct_call():
    # 1. Verify route configuration on the FastAPI app
    route = next((r for r in app.routes if r.path == "/api/v1/notifications/sse"), None)
    assert route is not None, "SSE route not found in app routes"
    assert "GET" in route.methods

    # Verify that the route depends on authentication
    dependency_calls = [dep.call for dep in route.dependant.dependencies]
    assert (
        get_current_active_user in dependency_calls
    ), "Route should depend on get_current_active_user"

    # 2. Verify direct invocation of the endpoint returns the correct StreamingResponse
    mock_user = User(id=99, email="sse_test@example.com")
    response = await sse_notifications(request=None, current_user=mock_user)

    assert isinstance(response, StreamingResponse)
    assert response.media_type == "text/event-stream"


@pytest.mark.anyio
async def test_sse_integration_recommendation(client: AsyncClient):
    # Ensure starting clean
    sse_manager.active_connections.clear()

    # 1. Setup Farmer
    farmer_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    assert farmer_profile.status_code == 200
    farmer_id = farmer_profile.json()["id"]

    # 2. Setup Advisor
    advisor_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer advisor-token"}
    )
    assert advisor_profile.status_code == 200
    advisor_id = advisor_profile.json()["id"]

    # 3. Create Campaign
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={
            "name": "SSE Campaign Rec",
            "start_date": "2026-06-01T00:00:00",
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # 4. Create Plot
    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "SSE Plot Rec",
            "area": 10.0,
            "campaign_id": campaign_id,
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert plot_res.status_code == 201
    plot_id = plot_res.json()["id"]

    # 5. Subscribe Farmer directly to the sse_manager
    events_received = []
    gen = sse_manager.subscribe(farmer_id)

    async def listen():
        try:
            val = await gen.__anext__()
            events_received.append(val)
        except StopAsyncIteration:
            pass
        except Exception as e:
            logger.error(f"Error in listen task: {e}")

    listen_task = asyncio.create_task(listen())
    await asyncio.sleep(0.05)  # Let connection register

    # 6. Advisor creates a recommendation on the Farmer's plot
    rec_data = {
        "plot_id": plot_id,
        "advisor_id": advisor_id,
        "content": "SSE Recommended Action: Irrigate plot tomorrow.",
        "priority": "HIGH",
    }
    create_rec_res = await client.post(
        "/api/v1/recommendations/",
        json=rec_data,
        headers={"Authorization": "Bearer advisor-token"},
    )
    assert create_rec_res.status_code == 201
    rec_id = create_rec_res.json()["id"]

    # 7. Wait for event to be processed by the background generator
    await asyncio.wait_for(listen_task, timeout=2.0)

    # 8. Assert SSE notification was received and has correct info
    assert len(events_received) == 1
    assert "new_recommendation" in events_received[0]
    assert str(rec_id) in events_received[0]
    assert "SSE Plot Rec" in events_received[0]

    # Clean up
    await gen.aclose()
    await asyncio.sleep(0.01)
    assert len(sse_manager.active_connections) == 0


@pytest.mark.anyio
async def test_sse_integration_event_update(client: AsyncClient, mock_calendar):
    # Ensure starting clean
    sse_manager.active_connections.clear()

    # 1. Setup Farmer
    farmer_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    assert farmer_profile.status_code == 200
    farmer_id = farmer_profile.json()["id"]

    # 2. Setup Admin
    admin_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer admin-token"}
    )
    assert admin_profile.status_code == 200

    # 3. Create Campaign
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={
            "name": "SSE Campaign Event",
            "start_date": "2026-06-01T00:00:00",
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # 4. Create Plot
    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "SSE Plot Event",
            "area": 12.0,
            "campaign_id": campaign_id,
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert plot_res.status_code == 201
    plot_id = plot_res.json()["id"]

    # 5. Create Event as Farmer
    event_data = {
        "title": "Initial Event",
        "description": "To be modified by Admin",
        "event_date": "2026-07-01T08:00:00",
        "plot_id": plot_id,
        "campaign_id": campaign_id,
        "created_by_id": farmer_id,
    }
    create_event_res = await client.post(
        "/api/v1/events/",
        json=event_data,
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert create_event_res.status_code == 201
    event_id = create_event_res.json()["id"]

    mock_calendar.sync_event.reset_mock()

    # 6. Subscribe Farmer directly to the sse_manager
    events_received = []
    gen = sse_manager.subscribe(farmer_id)

    async def listen():
        try:
            val = await gen.__anext__()
            events_received.append(val)
        except StopAsyncIteration:
            pass
        except Exception as e:
            logger.error(f"Error in listen task: {e}")

    listen_task = asyncio.create_task(listen())
    await asyncio.sleep(0.05)  # Let connection register

    # 7. Admin updates the event (non-owner) using PATCH
    update_data = {
        "title": "Updated Event Title",
        "description": "Modified description by Admin",
    }
    update_res = await client.patch(
        f"/api/v1/events/{event_id}",
        json=update_data,
        headers={"Authorization": "Bearer admin-token"},
    )
    assert update_res.status_code == 200

    # 8. Wait for event to be processed by the background generator
    await asyncio.wait_for(listen_task, timeout=2.0)

    # 9. Assert SSE notification received and has correct info
    assert len(events_received) == 1
    assert "event_updated" in events_received[0]
    assert str(event_id) in events_received[0]
    assert "Updated Event Title" in events_received[0]

    # Clean up
    await gen.aclose()
    await asyncio.sleep(0.01)
    assert len(sse_manager.active_connections) == 0
