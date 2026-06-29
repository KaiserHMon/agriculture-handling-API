import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_recommendation_advisor_success(client: AsyncClient):
    """
    Given an Advisor, a Farmer, and a Plot.
    When the Advisor posts a recommendation for that plot.
    Then the API should create it and return 201.
    """
    # 1. Setup Farmer
    farmer_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_id = farmer_profile.json()["id"]

    # 2. Setup Advisor
    advisor_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer advisor-token"}
    )
    advisor_id = advisor_profile.json()["id"]

    # 3. Create Campaign
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "Campaign R", "start_date": "2026-06-01T00:00:00", "user_id": farmer_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    campaign_id = camp_res.json()["id"]

    # 4. Create Plot
    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Plot R",
            "area": 22.0,
            "location": "Casilda",
            "campaign_id": campaign_id,
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    plot_id = plot_res.json()["id"]

    # 5. Advisor creates recommendation
    rec_data = {
        "plot_id": plot_id,
        "advisor_id": advisor_id,
        "content": "Apply fertilizer before rain",
        "priority": "HIGH",
    }

    create_res = await client.post(
        "/api/v1/recommendations/", json=rec_data, headers={"Authorization": "Bearer advisor-token"}
    )
    assert create_res.status_code == 201
    created_rec = create_res.json()
    assert created_rec["content"] == "Apply fertilizer before rain"
    assert created_rec["advisor_id"] == advisor_id


@pytest.mark.anyio
async def test_create_recommendation_farmer_forbidden(client: AsyncClient):
    """
    Given a Farmer.
    When they attempt to create a recommendation.
    Then the API should reject it with 403 Forbidden.
    """
    rec_data = {
        "plot_id": 1,
        "advisor_id": 1,
        "content": "Farmer recommendation",
        "priority": "LOW",
    }

    create_res = await client.post(
        "/api/v1/recommendations/", json=rec_data, headers={"Authorization": "Bearer farmer-token"}
    )
    assert create_res.status_code == 403


@pytest.mark.anyio
async def test_farmer_view_own_plot_recommendations(client: AsyncClient):
    """
    Given a Farmer who owns Plot X and a Recommendation Y on Plot X.
    When the Farmer gets recommendations for Plot X.
    Then the API should return Recommendation Y.
    """
    farmer_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_id = farmer_profile.json()["id"]
    advisor_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer advisor-token"}
    )
    advisor_id = advisor_profile.json()["id"]

    # Create Campaign
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "Campaign F", "start_date": "2026-06-01T00:00:00", "user_id": farmer_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    campaign_id = camp_res.json()["id"]

    # Create Plot
    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Farmer's Own Plot",
            "area": 10.0,
            "campaign_id": campaign_id,
            "user_id": farmer_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    plot_id = plot_res.json()["id"]

    # Advisor creates recommendation
    await client.post(
        "/api/v1/recommendations/",
        json={
            "plot_id": plot_id,
            "advisor_id": advisor_id,
            "content": "Water crops daily",
            "priority": "MEDIUM",
        },
        headers={"Authorization": "Bearer advisor-token"},
    )

    # Farmer retrieves recommendations for their plot
    get_res = await client.get(
        f"/api/v1/recommendations/plot/{plot_id}", headers={"Authorization": "Bearer farmer-token"}
    )
    assert get_res.status_code == 200
    recs = get_res.json()
    assert len(recs) == 1
    assert recs[0]["content"] == "Water crops daily"


@pytest.mark.anyio
async def test_farmer_cannot_view_other_plot_recommendations(client: AsyncClient):
    """
    Given Farmer 1 who owns Plot 1 and Farmer 2.
    When Farmer 2 requests recommendations for Plot 1.
    Then the API should reject it with 403 Forbidden.
    """
    farmer_1_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_1_id = farmer_1_profile.json()["id"]
    advisor_profile = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer advisor-token"}
    )
    advisor_id = advisor_profile.json()["id"]

    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "Campaign F1", "start_date": "2026-06-01T00:00:00", "user_id": farmer_1_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    campaign_id = camp_res.json()["id"]

    plot_res = await client.post(
        "/api/v1/plots/",
        json={
            "name": "Farmer 1 Plot",
            "area": 10.0,
            "campaign_id": campaign_id,
            "user_id": farmer_1_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    plot_id = plot_res.json()["id"]

    # Advisor creates recommendation
    await client.post(
        "/api/v1/recommendations/",
        json={
            "plot_id": plot_id,
            "advisor_id": advisor_id,
            "content": "Do not harvest yet",
            "priority": "LOW",
        },
        headers={"Authorization": "Bearer advisor-token"},
    )

    # Farmer 2 requests recommendations for Plot 1
    get_res = await client.get(
        f"/api/v1/recommendations/plot/{plot_id}",
        headers={"Authorization": "Bearer farmer-token-2"},
    )
    assert get_res.status_code == 403
