import os
import pytest
import logging
from fastapi.testclient import TestClient
from mcard.interfaces.api.mcard_api import app
from dotenv import load_dotenv
import pytest_asyncio
from httpx import AsyncClient
from mcard.domain.models.card import MCard

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Mock environment variables
os.environ['MCARD_API_KEY'] = 'test_api_key'

# Print the MCARD_API_KEY value for debugging
print(f"MCARD_API_KEY in test setup: {os.getenv('MCARD_API_KEY')}")

# Log the MCARD_API_KEY value after setting it
logging.debug(f"MCARD_API_KEY after setting: {os.getenv('MCARD_API_KEY')}")

# Initialize a single repository instance for all tests
from mcard.infrastructure.repository import SQLiteInMemoryRepository as InMemoryRepository
shared_repo = InMemoryRepository()

# Mock the get_repository function to return the shared repository instance
def mock_get_repository():
    return shared_repo

@pytest.fixture(autouse=True)
def setup_repo(monkeypatch):
    monkeypatch.setattr('mcard.infrastructure.repository.get_repository', mock_get_repository)
    monkeypatch.setattr('mcard.interfaces.api.mcard_api.get_repository', lambda: shared_repo)

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Test cases

@pytest.mark.asyncio
async def test_create_card(async_client):
    print(f"Shared repository instance ID: {id(shared_repo)}")
    # Use the session's query interface instead of a cursor
    card = MCard(content="Test content")
    await shared_repo.save(card)
    response = await async_client.post("/cards/", json={"content": "Test content"}, headers={"x-api-key": "test_api_key"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["content"] == "Test content"
    assert "hash" in response_data

@pytest.mark.asyncio
async def test_get_card(async_client):
    # First, create a card
    create_response = await async_client.post("/cards/", json={"content": "Test content"}, headers={"x-api-key": "test_api_key"})
    card_hash = create_response.json().get("hash")
    logging.debug(f"Hash from creation response: {card_hash}")
    logging.debug(f"Repository instance ID during creation: {id(shared_repo)}")
    print(f"Repository state after creation: {[card.hash for card in await shared_repo.get_all()]}")
    # Now, retrieve the card
    logging.debug(f"Repository instance ID during retrieval: {id(shared_repo)}")
    response = await async_client.get(f"/cards/{card_hash}", headers={"x-api-key": "test_api_key"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["content"] == "Test content"
    assert response_data["hash"] == card_hash

@pytest.mark.asyncio
async def test_list_cards(async_client):
    # List all cards
    response = await async_client.get("/cards/", headers={"x-api-key": "test_api_key"})
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)

@pytest.mark.asyncio
async def test_list_cards_by_content(async_client):
    # Create multiple cards
    contents = ["Content A", "Content B", "Content C"]
    for content in contents:
        await async_client.post("/cards/", json={"content": content}, headers={"x-api-key": "test_api_key"})

    # Retrieve all cards and filter by content
    response = await async_client.get("/cards/", headers={"x-api-key": "test_api_key"})
    assert response.status_code == 200
    response_data = response.json()
    retrieved_contents = [card["content"] for card in response_data]
    for content in contents:
        assert content in retrieved_contents

@pytest.mark.asyncio
async def test_list_cards_with_pagination(async_client):
    # Create multiple cards
    for i in range(10):
        await async_client.post("/cards/", json={"content": f"Content {i}"}, headers={"x-api-key": "test_api_key"})

    # Retrieve cards with pagination
    response = await async_client.get("/cards/?limit=5&offset=0", headers={"x-api-key": "test_api_key"})
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 5

    response = await async_client.get("/cards/?limit=5&offset=5", headers={"x-api-key": "test_api_key"})
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 5

@pytest.mark.asyncio
async def test_remove_card(async_client):
    # First, create a card
    create_response = await async_client.post("/cards/", json={"content": "Test content"}, headers={"x-api-key": "test_api_key"})
    card_hash = create_response.json().get("hash")
    logging.debug(f"Hash from creation response: {card_hash}")
    logging.debug(f"Repository instance ID during creation: {id(shared_repo)}")
    print(f"Repository state after creation: {[card.hash for card in await shared_repo.get_all()]}")
    # Now, remove the card
    response = await async_client.delete(f"/cards/{card_hash}", headers={"x-api-key": "test_api_key"})
    assert response.status_code == 200
    logging.debug(f"Repository instance ID during retrieval: {id(shared_repo)}")
    print(f"Repository state after deletion: {[card.hash for card in await shared_repo.get_all()]}")
    # Verify the card is removed
    response = await async_client.get(f"/cards/{card_hash}", headers={"x-api-key": "test_api_key"})
    assert response.status_code == 404
