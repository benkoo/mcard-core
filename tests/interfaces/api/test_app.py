"""
Tests for the MCard API interface.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from mcard.domain.models.card import MCard
from mcard.interfaces.api.app import app, get_card_repo
from mcard.domain.services.hashing import get_hashing_service, set_hashing_service

# Test data
TEST_CONTENT = "Test content"
TEST_HASH = "test_hash_123"
TEST_TIME = datetime.now(timezone.utc)
TEST_CARD = MCard(content=TEST_CONTENT, hash=TEST_HASH, g_time=TEST_TIME)

@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.get = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_by_time_range = AsyncMock()
    return repo

@pytest.fixture
def mock_hashing_service():
    """Create a mock hashing service."""
    service = AsyncMock()
    service.hash_content = AsyncMock(return_value=TEST_HASH)
    original_service = get_hashing_service()
    set_hashing_service(service)
    yield service
    set_hashing_service(original_service)

@pytest.fixture
def client(mock_repo, mock_hashing_service):
    """Create a test client with mock dependencies."""
    async def override_get_repo():
        return mock_repo
    
    app.dependency_overrides[get_card_repo] = override_get_repo
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_create_card(client, mock_repo, mock_hashing_service):
    """Test creating a new card."""
    mock_repo.save.return_value = None
    response = client.post("/cards/", json={"content": TEST_CONTENT})
    
    assert response.status_code == 200
    assert "hash" in response.json()
    assert "content" in response.json()
    assert "g_time" in response.json()
    assert response.json()["content"] == TEST_CONTENT
    
    mock_repo.save.assert_called_once()
    mock_hashing_service.hash_content.assert_called_once_with(TEST_CONTENT.encode('utf-8'))

def test_get_card_success(client, mock_repo):
    """Test getting an existing card."""
    mock_repo.get.return_value = TEST_CARD
    response = client.get(f"/cards/{TEST_HASH}")
    
    assert response.status_code == 200
    assert response.json()["hash"] == TEST_HASH
    assert response.json()["content"] == TEST_CONTENT
    assert "g_time" in response.json()
    
    mock_repo.get.assert_called_once_with(TEST_HASH)

def test_get_card_not_found(client, mock_repo):
    """Test getting a non-existent card."""
    mock_repo.get.return_value = None
    response = client.get(f"/cards/{TEST_HASH}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Card not found"
    
    mock_repo.get.assert_called_once_with(TEST_HASH)

def test_list_cards_no_filters(client, mock_repo):
    """Test listing cards without filters."""
    mock_repo.get_all.return_value = [TEST_CARD]
    response = client.get("/cards/")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["hash"] == TEST_HASH
    assert response.json()[0]["content"] == TEST_CONTENT
    
    mock_repo.get_all.assert_called_once_with(None, None)

def test_list_cards_with_time_range(client, mock_repo):
    """Test listing cards with time range filters."""
    mock_repo.get_by_time_range.return_value = [TEST_CARD]
    start_time = "2024-01-01T00:00:00Z"
    end_time = "2024-01-02T00:00:00Z"
    
    response = client.get(f"/cards/?start_time={start_time}&end_time={end_time}")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["hash"] == TEST_HASH
    
    mock_repo.get_by_time_range.assert_called_once()
