import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_plot_success_farmer(client: AsyncClient):
    """
    Given an authenticated Farmer and an active Campaign.
    When they create a plot for themselves under that campaign.
    Then the API should create it and return 201.
    """
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    assert profile_res.status_code == 200
    farmer_id = profile_res.json()["id"]

    # 1. Create Campaign
    campaign_data = {
        "name": "Summer Campaign",
        "description": "Main summer campaign",
        "start_date": "2026-06-01T00:00:00",
        "end_date": "2026-09-01T00:00:00",
        "user_id": farmer_id,
    }
    camp_res = await client.post(
        "/api/v1/campaigns/", json=campaign_data, headers={"Authorization": "Bearer farmer-token"}
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # 2. Create Plot
    plot_data = {
        "name": "Northern Field",
        "description": "Wheat field",
        "area": 12.5,
        "location": "Rosario",
        "campaign_id": campaign_id,
        "user_id": farmer_id,
    }

    create_res = await client.post(
        "/api/v1/plots/", json=plot_data, headers={"Authorization": "Bearer farmer-token"}
    )
    assert create_res.status_code == 201
    created_plot = create_res.json()
    assert created_plot["name"] == "Northern Field"
    assert created_plot["user_id"] == farmer_id

    # 3. Verify listing shows the plot
    list_res = await client.get("/api/v1/plots/", headers={"Authorization": "Bearer farmer-token"})
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == created_plot["id"]


@pytest.mark.anyio
async def test_create_plot_advisor_forbidden(client: AsyncClient):
    """
    Given an authenticated Advisor.
    When they attempt to create a plot.
    Then the API should reject it with 403 Forbidden.
    """
    plot_data = {
        "name": "Northern Field",
        "description": "Wheat field",
        "area": 12.5,
        "location": "Rosario",
        "campaign_id": 1,
        "user_id": 1,
    }
    create_res = await client.post(
        "/api/v1/plots/", json=plot_data, headers={"Authorization": "Bearer advisor-token"}
    )
    assert create_res.status_code == 403


@pytest.mark.anyio
async def test_farmer_cannot_access_other_farmer_plot(client: AsyncClient):
    """
    Given two Farmers (Farmer 1 and Farmer 2).
    When Farmer 1 owns Plot X.
    Then Farmer 2 should not be able to get, update, or delete Plot X.
    """
    # 1. Get IDs
    profile_res_1 = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_1_id = profile_res_1.json()["id"]

    # 2. Create Campaign for Farmer 1
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "F1 Campaign", "start_date": "2026-06-01T00:00:00", "user_id": farmer_1_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # 3. Create Plot for Farmer 1
    plot_data = {
        "name": "Farmer 1 Field",
        "area": 50.0,
        "location": "Pergamino",
        "campaign_id": campaign_id,
        "user_id": farmer_1_id,
    }
    create_res = await client.post(
        "/api/v1/plots/", json=plot_data, headers={"Authorization": "Bearer farmer-token"}
    )
    assert create_res.status_code == 201
    plot_id = create_res.json()["id"]

    # 4. Try to retrieve, update, or delete this plot using Farmer 2 credentials
    # Get plot
    get_res = await client.get(
        f"/api/v1/plots/{plot_id}", headers={"Authorization": "Bearer farmer-token-2"}
    )
    assert get_res.status_code == 403

    # Update plot
    update_res = await client.patch(
        f"/api/v1/plots/{plot_id}",
        json={"name": "Stolen Field"},
        headers={"Authorization": "Bearer farmer-token-2"},
    )
    assert update_res.status_code == 403

    # Delete plot
    delete_res = await client.delete(
        f"/api/v1/plots/{plot_id}", headers={"Authorization": "Bearer farmer-token-2"}
    )
    assert delete_res.status_code == 403


@pytest.mark.anyio
async def test_admin_can_access_any_plot(client: AsyncClient):
    """
    Given a plot owned by a Farmer.
    When an Admin requests the plot details or list.
    Then the Admin should have full access.
    """
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_id = profile_res.json()["id"]

    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Campaign for Admin test",
            "start_date": "2026-06-01T00:00:00",
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    create_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Farmer Field",
            "area": 35.0,
            "location": "Venado Tuerto",
            "campaign_id": campaign_id,
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert create_res.status_code == 201
    plot_id = create_res.json()["id"]

    # Admin lists plots
    list_res = await client.get("/api/v1/plots/", headers={"Authorization": "Bearer admin-token"})
    assert list_res.status_code == 200
    assert any(p["id"] == plot_id for p in list_res.json())

    # Admin gets plot
    get_res = await client.get(
        f"/api/v1/plots/{plot_id}", headers={"Authorization": "Bearer admin-token"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Farmer Field"


@pytest.mark.anyio
async def test_plot_report_triggers_weather_mock(client: AsyncClient, mock_weather):
    """
    Given a plot and a mocked Weather Service.
    When a client requests the agricultural plot report.
    Then the API should invoke the Weather Service mock and return the mock weather data.
    """
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_id = profile_res.json()["id"]

    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "Report Campaign", "start_date": "2026-06-01T00:00:00", "user_id": farmer_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    campaign_id = camp_res.json()["id"]

    create_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Weather Test Plot",
            "area": 10.0,
            "location": "Rosario",
            "campaign_id": campaign_id,
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    plot_id = create_res.json()["id"]

    # Request plot report
    report_res = await client.get(
        f"/api/v1/plots/{plot_id}/report", headers={"Authorization": "Bearer farmer-token"}
    )
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["plot_id"] == plot_id
    assert report_data["weather_forecast"]["conditions"] == "rainy"
    assert report_data["weather_forecast"]["temperature"] == 22.5

    # Assert that the mock_weather was indeed called with "Rosario"
    mock_weather.get_forecast.assert_called_once_with("Rosario")
