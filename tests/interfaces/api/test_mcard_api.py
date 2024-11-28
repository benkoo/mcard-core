import os
import pytest
import logging
from fastapi.testclient import TestClient
from mcard.interfaces.api.mcard_api import app, load_app_settings, get_repository
from dotenv import load_dotenv
import pytest_asyncio
from httpx import AsyncClient
from mcard.domain.models.card import MCard
from mcard.domain.models.config import AppSettings, DatabaseSettings
from mcard.infrastructure.persistence.schema_utils import initialize_schema
from pathlib import Path

# Set testing mode
os.environ['TESTING'] = 'true'

# Load test-specific environment variables
test_env_path = Path(__file__).parent.parent.parent / '.env.test'
load_dotenv(test_env_path, override=True)  # Add override=True to ensure test values take precedence

# Load AppSettings with required fields
test_settings = AppSettings(
    database=DatabaseSettings(
        db_path=":memory:",  # Use in-memory database for tests
        data_source="sqlite",
        pool_size=3,
        timeout=15.0
    ),
    mcard_api_key="test_custom_api_key_12345"  # Use the same API key as in the environment
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize a single repository instance for all tests
from mcard.infrastructure.persistence.sqlite import SQLiteRepository

@pytest_asyncio.fixture(scope="function", autouse=True)
async def shared_repo():
    """Create a fresh repository for each test."""
    repo = SQLiteRepository(db_path=':memory:')
    initialize_schema(repo.connection)
    try:
        yield repo
    finally:
        await repo.close_connection()

@pytest_asyncio.fixture
async def async_client(shared_repo):
    """Create an async test client."""
    app.dependency_overrides[load_app_settings] = lambda: test_settings
    app.dependency_overrides[get_repository] = lambda: shared_repo
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_card(async_client):
    """Test card creation."""
    response = await async_client.post(
        "/cards/",
        json={"content": "Test content"},
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    assert response.status_code == 201
    assert "hash" in response.json()

@pytest.mark.asyncio
async def test_get_card(async_client):
    # First, create a card
    create_response = await async_client.post(
        "/cards/",
        json={"content": "Test content"},
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    card_hash = create_response.json().get("hash")
    logging.debug(f"Hash from creation response: {card_hash}")

    # Get the card
    response = await async_client.get(
        f"/cards/{card_hash}",
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hash"] == card_hash
    assert data["content"] == "Test content"

@pytest.mark.asyncio
async def test_list_cards(async_client):
    # Create some test cards
    for i in range(3):
        await async_client.post(
            "/cards/",
            json={"content": f"Test content {i}"},
            headers={"x-api-key": test_settings.mcard_api_key}
        )

    response = await async_client.get(
        "/cards/",
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("Test content" in card["content"] for card in data)

@pytest.mark.asyncio
async def test_list_cards_by_content(async_client):
    # Create test cards with different content
    await async_client.post(
        "/cards/",
        json={"content": "Unique test content"},
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    await async_client.post(
        "/cards/",
        json={"content": "Different content"},
        headers={"x-api-key": test_settings.mcard_api_key}
    )

    response = await async_client.get(
        "/cards/?content=Unique",
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Unique" in data[0]["content"]

@pytest.mark.asyncio
async def test_list_cards_with_pagination(async_client):
    # Create test cards
    for i in range(5):
        await async_client.post(
            "/cards/",
            json={"content": f"Test content {i}"},
            headers={"x-api-key": test_settings.mcard_api_key}
        )

    response = await async_client.get(
        "/cards/?limit=2&offset=1",
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

@pytest.mark.asyncio
async def test_remove_card(async_client):
    # First, create a card
    create_response = await async_client.post(
        "/cards/",
        json={"content": "Test content"},
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    card_hash = create_response.json().get("hash")
    logging.debug(f"Hash from creation response: {card_hash}")

    # Delete the card
    response = await async_client.delete(
        f"/cards/{card_hash}",
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    assert response.status_code == 204

    # Verify card is deleted
    response = await async_client.get(
        f"/cards/{card_hash}",
        headers={"x-api-key": test_settings.mcard_api_key}
    )
    assert response.status_code == 404
