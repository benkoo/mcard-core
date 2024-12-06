"""Test suite for basic MCard JavaScript bridge server operations.

Requires Python 3.12 or higher.
"""
import sys

# Ensure minimum Python version
if sys.version_info < (3, 12):
    raise RuntimeError("This test suite requires Python 3.12 or higher")

import pytest
from httpx import AsyncClient, ASGITransport
import os
from pathlib import Path
from mcard.infrastructure.setup import MCardSetup
from mcard.config_constants import (
    DEFAULT_DB_PATH,
    TEST_DB_PATH as CONFIG_TEST_DB_PATH,
    DEFAULT_POOL_SIZE,
    DEFAULT_TIMEOUT,
    DEFAULT_API_PORT,
    ENV_DB_PATH,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_API_PORT,
    ENV_HASH_ALGORITHM,
    DEFAULT_HASH_ALGORITHM,
)

# Import the server module from examples
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bridge_server",
    str(Path(__file__).parent.parent.parent / "examples" / "bridge_to_javascript" / "src" / "server.py")
)
bridge_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge_server)
app = bridge_server.app

# Test configuration
TEST_API_KEY = "test_api_key"
TEST_DB_PATH = str(Path(__file__).parent / "data" / "test_mcard.db")
TEST_POOL_SIZE = DEFAULT_POOL_SIZE * 2  # Double the default for testing
TEST_TIMEOUT = DEFAULT_TIMEOUT  # Use default timeout

@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    # Store original environment variables
    original_env = {
        "MCARD_API_KEY": os.environ.get("MCARD_API_KEY"),
        ENV_DB_PATH: os.environ.get(ENV_DB_PATH),
        ENV_DB_MAX_CONNECTIONS: os.environ.get(ENV_DB_MAX_CONNECTIONS),
        ENV_DB_TIMEOUT: os.environ.get(ENV_DB_TIMEOUT),
        ENV_API_PORT: os.environ.get(ENV_API_PORT),
        ENV_HASH_ALGORITHM: os.environ.get(ENV_HASH_ALGORITHM),
    }
    
    # Set test environment variables
    os.environ["MCARD_API_KEY"] = TEST_API_KEY
    os.environ[ENV_DB_PATH] = TEST_DB_PATH
    os.environ[ENV_DB_MAX_CONNECTIONS] = str(TEST_POOL_SIZE)
    os.environ[ENV_DB_TIMEOUT] = str(TEST_TIMEOUT)
    os.environ[ENV_API_PORT] = str(DEFAULT_API_PORT)
    os.environ[ENV_HASH_ALGORITHM] = DEFAULT_HASH_ALGORITHM
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Setup test database."""
    # Ensure test data directory exists
    Path(TEST_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    # Remove test database if it exists
    try:
        Path(TEST_DB_PATH).unlink(missing_ok=True)
    except Exception:
        pass
        
    # Create a new setup instance with test database
    setup = MCardSetup(
        db_path=TEST_DB_PATH,
        max_connections=TEST_POOL_SIZE,
        timeout=TEST_TIMEOUT
    )
    
    # Initialize database
    await setup.initialize()
    
    # Update app's setup instance
    app.state.setup = setup
    
    yield
    
    await setup.cleanup()
    try:
        Path(TEST_DB_PATH).unlink(missing_ok=True)
    except Exception:
        pass

@pytest.fixture
async def async_client():
    """Create async client for testing."""
    # Reset the API key in the app
    app.state.api_key = TEST_API_KEY
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test health check endpoint."""
    response = await async_client.get(
        "/health",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_invalid_api_key(async_client):
    """Test invalid API key."""
    response = await async_client.get(
        "/health",
        headers={"X-API-Key": "invalid_key"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"

@pytest.mark.asyncio
async def test_create_card(async_client):
    """Test creating a card."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": "Test content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test content"
    assert "hash" in data
    assert "g_time" in data

@pytest.mark.asyncio
async def test_get_card(async_client):
    """Test getting a card."""
    # First create a card
    create_response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": "Test content"}
    )
    assert create_response.status_code == 200
    card_hash = create_response.json()["hash"]
    
    # Then get the card
    get_response = await async_client.get(
        f"/cards/{card_hash}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["content"] == "Test content"
    assert data["hash"] == card_hash

@pytest.mark.asyncio
async def test_list_cards(async_client):
    """Test listing cards."""
    # Create a few cards
    contents = ["Test 1", "Test 2", "Test 3"]
    for content in contents:
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
    
    # List all cards
    response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(contents)
    assert all(card["content"] in contents for card in data)

@pytest.mark.asyncio
async def test_delete_card(async_client):
    """Test deleting a card."""
    # First create a card
    create_response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": "Test content"}
    )
    assert create_response.status_code == 200
    card_hash = create_response.json()["hash"]
    
    # Then delete the card
    delete_response = await async_client.delete(
        f"/cards/{card_hash}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert delete_response.status_code == 200
    
    # Verify card is deleted
    get_response = await async_client.get(
        f"/cards/{card_hash}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_create_card_empty_content(async_client):
    """Test creating a card with empty content."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": ""}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == ""
    assert "hash" in data

@pytest.mark.asyncio
async def test_create_card_missing_content(async_client):
    """Test creating a card with missing content field."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_delete_nonexistent_card(async_client):
    """Test deleting a non-existent card."""
    response = await async_client.delete(
        "/cards/nonexistent",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_cards_empty_db(async_client):
    """Test listing cards with empty database."""
    response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
