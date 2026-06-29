import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_event_success_farmer(client: AsyncClient, mock_calendar):
    """
    Given a Farmer who owns a Campaign and a Plot.
    When the Farmer creates an event for that plot.
    Then the API should create it and return 201, and trigger the calendar sync mock.
    """
    # 1. Setup Farmer
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    assert profile_res.status_code == 200
    farmer_id = profile_res.json()["id"]

    # 2. Create Campaign
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "Campaign E", "start_date": "2026-06-01T00:00:00", "user_id": farmer_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    campaign_id = camp_res.json()["id"]

    # 3. Create Plot
    plot_res = await client.post(
        "/api/v1/plots/",
        json={"name": "Plot E", "area": 15.0, "campaign_id": campaign_id, "user_id": farmer_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    plot_id = plot_res.json()["id"]

    # 4. Create Event
    event_data = {
        "title": "Sowing corn",
        "description": "Start sowing the corn fields",
        "event_date": "2026-07-01T08:00:00",
        "plot_id": plot_id,
        "campaign_id": campaign_id,
        "created_by_id": farmer_id,
    }

    create_res = await client.post(
        "/api/v1/events/", json=event_data, headers={"Authorization": "Bearer farmer-token"}
    )
    assert create_res.status_code == 201
    created_event = create_res.json()
    assert created_event["title"] == "Sowing corn"

    # 5. Verify the Google Calendar sync mock was called with the correct parameters
    from datetime import datetime

    mock_calendar.sync_event.assert_called_once()
    call_kwargs = mock_calendar.sync_event.call_args[1]
    assert call_kwargs["event_id"] == created_event["id"]
    assert call_kwargs["title"] == "Sowing corn"

    expected_dt = datetime.fromisoformat(created_event["event_date"].replace("Z", "+00:00"))
    actual_dt = call_kwargs["start_time"]
    # Normalize and compare
    assert actual_dt.isoformat() == expected_dt.isoformat()


@pytest.mark.anyio
async def test_create_event_other_plot_forbidden(client: AsyncClient, mock_calendar):
    """
    Given Farmer 1 who owns Plot 1, and Farmer 2.
    When Farmer 2 attempts to create an event on Plot 1.
    Then the API should reject it with 403 Forbidden, and not trigger calendar sync.
    """
    profile_res_1 = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_1_id = profile_res_1.json()["id"]
    profile_res_2 = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token-2"}
    )
    farmer_2_id = profile_res_2.json()["id"]

    # Create Campaign for Farmer 1
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "Campaign E1", "start_date": "2026-06-01T00:00:00", "user_id": farmer_1_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    campaign_id = camp_res.json()["id"]

    # Create Plot for Farmer 1
    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Farmer 1 Plot",
            "area": 15.0,
            "campaign_id": campaign_id,
            "user_id": farmer_1_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    plot_id = plot_res.json()["id"]

    # Farmer 2 tries to create event on Farmer 1's plot
    event_data = {
        "title": "Illegal sowing",
        "description": "Trying to sow on another plot",
        "event_date": "2026-07-01T08:00:00",
        "plot_id": plot_id,
        "campaign_id": campaign_id,
        "created_by_id": farmer_2_id,
    }

    create_res = await client.post(
        "/api/v1/events/", json=event_data, headers={"Authorization": "Bearer farmer-token-2"}
    )
    assert create_res.status_code == 403
    mock_calendar.sync_event.assert_not_called()
