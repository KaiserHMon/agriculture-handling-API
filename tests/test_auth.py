import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_auth_verify_admin_success(client: AsyncClient):
    """
    Given an endpoint requiring authentication.
    When a request is made with the mock 'admin-token'.
    Then the server should identify the user as an ADMIN.
    """
    response = await client.get(
        "/api/v1/auth/verify", headers={"Authorization": "Bearer admin-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True

    # Check profile endpoint to verify correct role mapping
    profile_response = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer admin-token"}
    )
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["role"] == "admin"
    assert profile_data["email"] == "admin@example.com"


@pytest.mark.anyio
async def test_auth_verify_farmer_success(client: AsyncClient):
    """
    Given an endpoint requiring authentication.
    When a request is made with the mock 'farmer-token'.
    Then the server should identify the user as a FARMER.
    """
    response = await client.get(
        "/api/v1/auth/verify", headers={"Authorization": "Bearer farmer-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True

    profile_response = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer farmer-token"}
    )
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["role"] == "farmer"


@pytest.mark.anyio
async def test_auth_verify_advisor_success(client: AsyncClient):
    """
    Given an endpoint requiring authentication.
    When a request is made with the mock 'advisor-token'.
    Then the server should identify the user as an ADVISOR.
    """
    response = await client.get(
        "/api/v1/auth/verify", headers={"Authorization": "Bearer advisor-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True

    profile_response = await client.get(
        "/api/v1/auth/profile", headers={"Authorization": "Bearer advisor-token"}
    )
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["role"] == "advisor"


@pytest.mark.anyio
async def test_auth_verify_invalid_token(client: AsyncClient):
    """
    Given an endpoint requiring authentication.
    When a request is made with an invalid token.
    Then the server should return 401 Unauthorized.
    """
    response = await client.get(
        "/api/v1/auth/verify", headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401
