import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_campaign_success_farmer(client: AsyncClient):
    """
    Given an authenticated Farmer.
    When they create a campaign for themselves.
    Then the API should create it and return 201.
    """
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    assert profile_res.status_code == 200
    farmer_id = profile_res.json()["id"]

    campaign_data = {
        "name": "Wheat Campaign 2026",
        "description": "Main wheat campaign of the year",
        "start_date": "2026-06-01T00:00:00",
        "end_date": "2026-12-01T00:00:00",
        "user_id": farmer_id,
    }

    create_res = await client.post(
        "/api/v1/campaigns/", json=campaign_data, headers={"Authorization": "Bearer farmer-token"}
    )
    assert create_res.status_code == 201
    created_camp = create_res.json()
    assert created_camp["name"] == "Wheat Campaign 2026"
    assert created_camp["user_id"] == farmer_id


@pytest.mark.anyio
async def test_farmer_cannot_access_other_farmer_campaign(client: AsyncClient):
    """
    Given Farmer 1 and Farmer 2.
    When Farmer 1 creates a campaign.
    Then Farmer 2 should be rejected with 403 or 404 when trying to view/modify it.
    """
    # 1. Get Farmer 1 profile
    profile_1 = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_1_id = profile_1.json()["id"]

    # 2. Create Campaign for Farmer 1
    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={
            "name": "Farmer 1 Private Campaign",
            "start_date": "2026-06-01T00:00:00",
            "user_id": farmer_1_id,
        },
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # 3. Farmer 2 attempts to get Farmer 1's campaign
    get_res = await client.get(
        f"/api/v1/campaigns/{campaign_id}", headers={"Authorization": "Bearer farmer-token-2"}
    )
    assert get_res.status_code in [403, 404]

    # 4. Farmer 2 attempts to update Farmer 1's campaign
    update_res = await client.patch(
        f"/api/v1/campaigns/{campaign_id}",
        json={"name": "Hacked Campaign"},
        headers={"Authorization": "Bearer farmer-token-2"},
    )
    assert update_res.status_code in [403, 404, 405]

    # 5. Farmer 2 attempts to delete Farmer 1's campaign
    delete_res = await client.delete(
        f"/api/v1/campaigns/{campaign_id}", headers={"Authorization": "Bearer farmer-token-2"}
    )
    assert delete_res.status_code in [403, 404, 405]


@pytest.mark.anyio
async def test_admin_can_access_any_campaign(client: AsyncClient):
    """
    Given a campaign created by a Farmer.
    When an Admin requests the campaign.
    Then the Admin should have full access.
    """
    profile_res = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    farmer_id = profile_res.json()["id"]

    camp_res = await client.post(
        "/api/v1/campaigns/",
        json={"name": "Farmer Campaign", "start_date": "2026-06-01T00:00:00", "user_id": farmer_id},
        headers={"Authorization": "Bearer farmer-token"},
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # Admin gets campaign
    get_res = await client.get(
        f"/api/v1/campaigns/{campaign_id}", headers={"Authorization": "Bearer admin-token"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Farmer Campaign"
