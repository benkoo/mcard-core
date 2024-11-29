import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime
import os

def test_health_check(test_client: TestClient):
    """Test the health check endpoint using sync client."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "database_connected" in data
    
    # Check field values
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["database_connected"] is True
    
    # Verify timestamp is a valid ISO format
    datetime.fromisoformat(data["timestamp"])

@pytest.mark.asyncio
async def test_health_check_async(async_client: AsyncClient):
    """Test the health check endpoint using async client."""
    async for client in async_client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "database_connected" in data
        
        # Check field values
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["database_connected"] is True
        
        # Verify timestamp is a valid ISO format
        datetime.fromisoformat(data["timestamp"])

@pytest.mark.asyncio
async def test_health_check_db_failure(async_client: AsyncClient, monkeypatch):
    """Test health check when database connection fails."""
    # Mock the get_repository function to raise an exception
    async def mock_get_repository():
        raise Exception("Database connection failed")
    
    from mcard_storage_service import get_repository
    monkeypatch.setattr("mcard_storage_service.get_repository", mock_get_repository)
    
    async for client in async_client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["database_connected"] is False
        assert data["version"] == "1.0.0"
        datetime.fromisoformat(data["timestamp"])
