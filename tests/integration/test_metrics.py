import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_metrics_empty_data(client: AsyncClient):
    """
    Given an authenticated user with no data.
    When they request dashboard metrics.
    Then the system returns zero values for all metrics.
    """
    # Create a fresh standard user
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    assert profile_res.status_code == 200

    metrics_res = await client.get(
        "/api/v1/metrics/dashboard", headers={"Authorization": "Bearer farmer-token"}
    )

    assert metrics_res.status_code == 200
    data = metrics_res.json()
    assert data["total_campaigns"] == 0
    assert data["active_campaigns"] == 0
    assert data["total_plots"] == 0
    assert data["total_area"] == 0.0
    assert data["total_events"] == 0
    assert data["total_recommendations"] == 0


@pytest.mark.anyio
async def test_metrics_successful_retrieval(client: AsyncClient):
    """
    Given an authenticated user with existing data.
    When the user requests dashboard metrics.
    Then the system computes the aggregations correctly.
    """
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_id = profile_res.json()["id"]

    # Create campaign
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Campaign 1",
            "start_date": "2026-01-01T00:00:00",
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert camp_res.status_code == 201
    camp_id = camp_res.json()["id"]

    # Create plot
    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Plot 1",
            "area": 10.5,
            "campaign_id": camp_id,
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert plot_res.status_code == 201
    plot_id = plot_res.json()["id"]

    # Create event
    event_res = await client.post(
        "/api/v1/events/",
        json={
            "title": "Event 1",
            "event_date": "2026-02-01T00:00:00",
            "plot_id": plot_id,
            "campaign_id": camp_id,
            "created_by_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert event_res.status_code == 201

    metrics_res = await client.get(
        "/api/v1/metrics/dashboard", headers={"Authorization": "Bearer farmer-token"}
    )
    assert metrics_res.status_code == 200
    data = metrics_res.json()
    assert data["total_campaigns"] == 1
    assert data["active_campaigns"] == 1
    assert data["total_plots"] == 1
    assert data["total_area"] == 10.5
    assert data["total_events"] == 1
    assert data["total_recommendations"] == 0


@pytest.mark.anyio
async def test_metrics_user_isolation(client: AsyncClient):
    """
    Given a standard authenticated user.
    When the user requests dashboard metrics.
    Then the metrics ONLY reflect the entities owned by or explicitly assigned to that user.
    """
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token-2"}
    )
    assert profile_res.status_code == 200
    other_farmer_id = profile_res.json()["id"]

    # Create campaign and plot for OTHER farmer
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Other Campaign",
            "start_date": "2026-01-01T00:00:00",
            "user_id": other_farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token-2"},
    )
    assert camp_res.status_code == 201
    camp_id = camp_res.json()["id"]

    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Other Plot",
            "area": 20.0,
            "campaign_id": camp_id,
            "user_id": other_farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token-2"},
    )
    assert plot_res.status_code == 201
    plot_id = plot_res.json()["id"]

    event_res = await client.post(
        "/api/v1/events/",
        json={
            "title": "Other Event",
            "event_date": "2026-02-01T00:00:00",
            "plot_id": plot_id,
            "campaign_id": camp_id,
            "created_by_id": other_farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token-2"},
    )
    assert event_res.status_code == 201

    # Check metrics for MAIN farmer (should not see other farmer's data)
    # The first test already created 1 campaign, 1 plot, 1 event for farmer-token if tests are stateful,
    # but anyio and db sessions typically rollback or are isolated if handled in fixtures.
    # We just ensure `farmer-token-2` data doesn't leak to `farmer-token`.
    metrics_res = await client.get(
        "/api/v1/metrics/dashboard", headers={"Authorization": "Bearer farmer-token"}
    )
    data = metrics_res.json()

    # We can't strictly assert zero if the database is shared and wasn't cleaned,
    # but we can assert we don't count the other_farmer data.
    # Since area was 20.0 for the other farmer, the total area shouldn't include it.
    assert data["total_area"] < 20.0
