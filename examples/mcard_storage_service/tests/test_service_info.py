import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

def test_service_info_requires_auth(test_client: TestClient):
    """Test that service info endpoint requires authentication."""
    response = test_client.get("/info")
    assert response.status_code == 401

def test_service_info_with_auth(test_client: TestClient, auth_headers):
    """Test that service info endpoint works with valid authentication."""
    response = test_client.get("/info", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "total_requests" in data
    assert "uptime" in data

@pytest.mark.asyncio
async def test_service_info_metrics_increment(async_client: AsyncClient, auth_headers):
    """Test that service metrics are properly tracked."""
    async for client in async_client:
        # Make initial request to get baseline
        response1 = await client.get("/info", headers=auth_headers)
        assert response1.status_code == 200
        initial_requests = response1.json()["total_requests"]

        # Make another request
        await client.get("/health")

        # Check that metrics have been updated
        response2 = await client.get("/info", headers=auth_headers)
        assert response2.status_code == 200
        updated_requests = response2.json()["total_requests"]
        assert updated_requests > initial_requests
