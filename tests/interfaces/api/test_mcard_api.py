"""Test MCard API."""
import os
import pytest
import pytest_asyncio
import logging
from fastapi.testclient import TestClient
from pathlib import Path
from mcard.domain.models.card import MCard
from mcard.interfaces.api.mcard_api import MCardAPI, app
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig
from mcard.config_constants import DEFAULT_DB_PATH, TEST_DB_PATH, DEFAULT_API_PORT, DEFAULT_API_KEY, ENV_DB_PATH, ENV_API_PORT, ENV_API_KEY
from http import HTTPStatus

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@pytest_asyncio.fixture(scope="function")
async def shared_repo(async_repository):
    """Create API instance with test database."""
    async with async_repository as repo:
        api = MCardAPI()
        yield api

@pytest.mark.asyncio
async def test_create_card(shared_repo):
    """Test creating a card."""
    api = shared_repo
    content = "Test content"
    card = await api.create_card(content)
    assert card.content == content

@pytest.mark.asyncio
async def test_get_card(shared_repo):
    """Test getting a card."""
    api = shared_repo
    content = "Test content"
    card = await api.create_card(content)
    retrieved = await api.get_card(card.hash)
    assert retrieved.content == content

@pytest.mark.asyncio
async def test_list_cards(shared_repo):
    """Test listing cards."""
    api = shared_repo
    cards = []
    for i in range(5):
        card = await api.create_card(f"Content {i}")
        cards.append(card)
    
    # Validate the cards are listed correctly
    retrieved_cards = await api.list_cards(page=1, page_size=10)
    assert len(retrieved_cards) == 5

@pytest.mark.asyncio
async def test_list_cards_by_content(shared_repo):
    """Test listing cards by content."""
    api = shared_repo
    await api.create_card("First card")
    await api.create_card("Second card")
    await api.create_card("Third card")
    await api.create_card("Another one")
    
    # Search for cards containing "card"
    cards = await api.list_cards(content="card")
    assert len(cards) == 3
    
    # Search for cards containing "one"
    cards = await api.list_cards(content="one")
    assert len(cards) == 1

@pytest.mark.asyncio
async def test_list_cards_with_pagination(shared_repo):
    """Test listing cards with pagination."""
    api = shared_repo
    for i in range(10):
        await api.create_card(f"Content {i}")
    
    # Test limit
    cards = await api.list_cards(limit=5)
    assert len(cards) == 5
    
    # Test offset
    cards = await api.list_cards(offset=5, limit=5)
    assert len(cards) == 5

@pytest.mark.asyncio
async def test_remove_card(shared_repo):
    """Test removing a card."""
    api = shared_repo
    content = "Test content"
    card = await api.create_card(content)
    
    # Verify card exists
    assert await api.get_card(card.hash) is not None
    
    # Remove card
    await api.remove_card(card.hash)
    
    # Verify card is removed
    assert await api.get_card(card.hash) is None

@pytest.mark.asyncio
async def test_create_card_large_content(shared_repo):
    """Test creating a card with large content."""
    api = shared_repo
    content = "x" * 1000000  # 1MB of content
    card = await api.create_card(content)
    assert card.content == content

@pytest.mark.asyncio
async def test_create_card_binary_content(shared_repo):
    """Test creating a card with binary content."""
    api = shared_repo
    content = b"Binary content"
    card = await api.create_card(content)
    assert card.content == content

@pytest.mark.asyncio
async def test_singleton_instance():
    instance1 = MCardAPI()
    instance2 = MCardAPI()
    assert instance1 is instance2, "MCardAPI is not a singleton!"

@pytest.mark.asyncio
async def test_database_path():
    assert DEFAULT_DB_PATH == TEST_DB_PATH

@pytest.mark.asyncio
async def test_api_health_status():
    response = client.get("/status")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["status"] == "healthy"

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_module():
    # Any setup needed before tests run
    os.environ[ENV_DB_PATH] = TEST_DB_PATH  # Use the test database path
    os.environ[ENV_API_PORT] = str(DEFAULT_API_PORT)  # Use the default API port
    yield  # This allows the tests to run

    # Any teardown needed after tests run
    del os.environ[ENV_DB_PATH]
    del os.environ[ENV_API_PORT]

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "port" in data
    assert "database_path" in data
    assert data["status"] == "healthy"
    assert data["port"] == str(DEFAULT_API_PORT)
    assert data["database_path"] == TEST_DB_PATH

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "port" in data
    assert "database_path" in data
    assert data["status"] == "healthy"
    assert data["port"] == str(DEFAULT_API_PORT)
    assert data["database_path"] == TEST_DB_PATH

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "port" in data
    assert "database_path" in data
    assert data["status"] == "healthy"
    assert data["port"] == str(DEFAULT_API_PORT)
    assert data["database_path"] == TEST_DB_PATH

@pytest.mark.asyncio
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
def test_shutdown():
    response = client.post("/shutdown")
    assert response.status_code == 200
    assert response.json() == {"message": "Server shutting down"}

def test_create_card():
    response = client.post("/cards/", json={"content": "Test content"})
    assert response.status_code == 200
    assert "hash" in response.json()

def test_get_card():
    create_response = client.post("/cards/", json={"content": "Test content"})
    card_hash = create_response.json()["hash"]
    response = client.get(f"/cards/{card_hash}")
    assert response.status_code == 200
    assert response.json()["hash"] == card_hash

def test_list_cards():
    response = client.get("/cards/?page=1&page_size=10")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)

def test_delete_card():
    create_response = client.post("/cards/", json={"content": "Test content"})
    card_hash = create_response.json()["hash"]
    delete_response = client.delete(f"/cards/{card_hash}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Card deleted"}
