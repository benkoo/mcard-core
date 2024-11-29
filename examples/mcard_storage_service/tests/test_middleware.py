import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import asyncio

def test_middleware_health_no_auth(test_client: TestClient):
    """Test that health endpoint doesn't require authentication."""
    response = test_client.get("/health")
    assert response.status_code == 200

def test_middleware_missing_api_key(test_client: TestClient):
    """Test endpoints fail when API key is missing."""
    response = test_client.get("/info")
    assert response.status_code == 401
    assert response.text == "API key is required"

    response = test_client.get("/cards/")
    assert response.status_code == 401
    assert response.text == "API key is required"

@pytest.mark.asyncio
async def test_middleware_request_tracking(async_client: AsyncClient):
    """Test that request tracking increments properly."""
    api_key = "test_api_key_12345"
    
    async for client in async_client:
        # Make initial request and get total_requests
        response = await client.get("/info", headers={"X-API-Key": api_key})
        assert response.status_code == 200
        initial_requests = response.json()["total_requests"]
        
        # Make another request and verify count increased
        response = await client.get("/info", headers={"X-API-Key": api_key})
        assert response.status_code == 200
        assert response.json()["total_requests"] > initial_requests

@pytest.mark.asyncio
async def test_middleware_concurrent_requests(async_client: AsyncClient):
    """Test that request tracking works correctly with concurrent requests."""
    api_key = "test_api_key_12345"
    
    async for client in async_client:
        # Get initial request count
        response = await client.get("/info", headers={"X-API-Key": api_key})
        initial_count = response.json()["total_requests"]
        
        # Make multiple concurrent requests
        tasks = []
        for _ in range(5):
            tasks.append(client.get("/info", headers={"X-API-Key": api_key}))
        
        responses = await asyncio.gather(*tasks)
        
        # All responses should be successful
        assert all(r.status_code == 200 for r in responses)
        
        # Get final count
        response = await client.get("/info", headers={"X-API-Key": api_key})
        final_count = response.json()["total_requests"]
        
        # Should have increased by at least the number of requests made
        assert final_count > initial_count
        assert final_count >= initial_count + 7  # 5 concurrent + 2 count checks

@pytest.mark.asyncio
async def test_middleware_invalid_api_key(async_client: AsyncClient):
    """Test middleware behavior with invalid API key."""
    async for client in async_client:
        # Test with invalid API key
        response = await client.get("/info", headers={"X-API-Key": "invalid_key"})
        assert response.status_code == 403
        
        # Test with malformed API key header
        response = await client.get("/info", headers={"x-api-key": ""})
        assert response.status_code == 401
        
        # Test with missing API key header
        response = await client.get("/info", headers={})
        assert response.status_code == 401
