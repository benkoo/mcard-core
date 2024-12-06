"""Test suite for configuration and performance in MCard JavaScript bridge server.

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
import asyncio
import random
from datetime import datetime
from mcard.infrastructure.setup import MCardSetup
from mcard.config_constants import (
    DEFAULT_POOL_SIZE,
    DEFAULT_TIMEOUT,
    DEFAULT_API_PORT,
    ENV_DB_PATH,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_API_PORT,
    ENV_HASH_ALGORITHM,
    DEFAULT_HASH_ALGORITHM,
    ENV_HASH_CUSTOM_MODULE,
    ENV_HASH_CUSTOM_FUNCTION,
    ENV_HASH_CUSTOM_LENGTH,
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
TEST_POOL_SIZE = DEFAULT_POOL_SIZE * 2
TEST_TIMEOUT = DEFAULT_TIMEOUT

@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    original_env = {
        "MCARD_API_KEY": os.environ.get("MCARD_API_KEY"),
        ENV_DB_PATH: os.environ.get(ENV_DB_PATH),
        ENV_DB_MAX_CONNECTIONS: os.environ.get(ENV_DB_MAX_CONNECTIONS),
        ENV_DB_TIMEOUT: os.environ.get(ENV_DB_TIMEOUT),
        ENV_API_PORT: os.environ.get(ENV_API_PORT),
        ENV_HASH_ALGORITHM: os.environ.get(ENV_HASH_ALGORITHM),
    }
    
    os.environ["MCARD_API_KEY"] = TEST_API_KEY
    os.environ[ENV_DB_PATH] = TEST_DB_PATH
    os.environ[ENV_DB_MAX_CONNECTIONS] = str(TEST_POOL_SIZE)
    os.environ[ENV_DB_TIMEOUT] = str(TEST_TIMEOUT)
    os.environ[ENV_API_PORT] = str(DEFAULT_API_PORT)
    os.environ[ENV_HASH_ALGORITHM] = DEFAULT_HASH_ALGORITHM
    
    yield
    
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

@pytest.fixture(autouse=True)
async def setup_test_db(request):
    """Setup test database."""
    # Skip cleanup if we're running the hundred cards test
    skip_cleanup = request.node.name == "test_create_hundred_cards"
    
    Path(TEST_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        Path(TEST_DB_PATH).unlink(missing_ok=True)
    except Exception:
        pass
        
    setup = MCardSetup(
        db_path=TEST_DB_PATH,
        max_connections=TEST_POOL_SIZE,
        timeout=TEST_TIMEOUT
    )
    
    await setup.initialize()
    app.state.setup = setup
    
    yield
    
    if not skip_cleanup:
        await setup.cleanup()
        try:
            Path(TEST_DB_PATH).unlink(missing_ok=True)
        except Exception:
            pass

@pytest.fixture
async def async_client():
    """Create async client for testing."""
    app.state.api_key = TEST_API_KEY
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_bulk_card_operations(async_client):
    """Test creating, listing, and deleting hundreds of cards."""
    # Create 200 cards
    card_count = 200
    contents = [f"Test content {i}" for i in range(card_count)]
    card_hashes = []
    
    # Create cards
    for content in contents:
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        card_hashes.append(response.json()["hash"])
    
    # List all cards
    response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == card_count
    
    # Delete all cards
    for card_hash in card_hashes:
        response = await async_client.delete(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_concurrent_card_operations(async_client):
    """Test concurrent creation and deletion of cards."""
    card_count = 50
    contents = [f"Concurrent test content {i}" for i in range(card_count)]
    
    async def create_card(content):
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        return response.json()["hash"]
    
    # Create cards concurrently
    tasks = [create_card(content) for content in contents]
    card_hashes = await asyncio.gather(*tasks)
    
    # Verify all cards were created
    response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == card_count
    
    # Delete cards concurrently
    async def delete_card(card_hash):
        response = await async_client.delete(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200
    
    delete_tasks = [delete_card(card_hash) for card_hash in card_hashes]
    await asyncio.gather(*delete_tasks)

@pytest.mark.asyncio
async def test_create_hundred_cards(async_client):
    """Create 100 MCards with varied content and leave them in the database."""
    # Content templates
    html_template = """
    <!DOCTYPE html>
    <html>
    <head><title>Card {}</title></head>
    <body><h1>Card {}</h1><p>{}</p></body>
    </html>
    """
    
    js_template = """
    // Card {} JavaScript
    function processCard{0}() {{
        console.log("{1}");
        return {2};
    }}
    """
    
    sql_template = """
    -- Card {} SQL
    CREATE TABLE IF NOT EXISTS card_{0} (
        id INTEGER PRIMARY KEY,
        value TEXT
    );
    INSERT INTO card_{0} (value) VALUES ('{1}');
    """
    
    python_template = """
    # Card {} Python
    def process_card_{}():
        value = "{}"
        return {{"card_id": {}, "value": value}}
    """
    
    # Generate 100 cards with different content types
    card_count = 100
    created_hashes = []
    
    for i in range(card_count):
        content_type = i % 4  # Rotate through 4 content types
        timestamp = datetime.now().isoformat()
        
        if content_type == 0:
            # HTML content
            content = html_template.format(i, i, f"Created at {timestamp}")
        elif content_type == 1:
            # JavaScript content
            content = js_template.format(i, f"Processing card {i}", f"{{'timestamp': '{timestamp}'}}")
        elif content_type == 2:
            # SQL content
            content = sql_template.format(i, timestamp)
        else:
            # Python content
            content = python_template.format(i, i, timestamp, i)
        
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        created_hashes.append(response.json()["hash"])
    
    # Verify all cards were created
    response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == card_count
    
    # Verify each card can be retrieved
    for card_hash in created_hashes:
        response = await async_client.get(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_custom_hash_configuration(async_client):
    """Test custom hash configuration."""
    # Set custom hash configuration
    os.environ[ENV_HASH_ALGORITHM] = "custom"
    os.environ[ENV_HASH_CUSTOM_MODULE] = "hashlib"
    os.environ[ENV_HASH_CUSTOM_FUNCTION] = "md5"
    os.environ[ENV_HASH_CUSTOM_LENGTH] = "32"
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": "Test content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["hash"]) == 32

@pytest.mark.asyncio
async def test_custom_port_configuration(async_client):
    """Test port configuration."""
    test_port = 8081
    os.environ[ENV_API_PORT] = str(test_port)
    
    # Create a new app instance with custom port
    new_app = bridge_server.create_app()
    assert new_app.state.port == test_port
    
    # Test with custom port
    transport = ASGITransport(app=new_app)
    async with AsyncClient(transport=transport, base_url=f"http://test:{test_port}") as client:
        response = await client.get(
            "/health",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_database_configuration(async_client):
    """Test database configuration."""
    # Test with custom database configuration
    custom_db_path = str(Path(TEST_DB_PATH).parent / "custom_test.db")
    custom_pool_size = 10
    custom_timeout = 30.0
    
    os.environ[ENV_DB_PATH] = custom_db_path
    os.environ[ENV_DB_MAX_CONNECTIONS] = str(custom_pool_size)
    os.environ[ENV_DB_TIMEOUT] = str(custom_timeout)
    
    # Create a new app instance with custom database configuration
    new_app = bridge_server.create_app()
    setup = new_app.state.setup
    
    assert setup.db_path == custom_db_path
    assert setup.max_connections == custom_pool_size
    assert setup.timeout == custom_timeout
    
    # Clean up
    try:
        Path(custom_db_path).unlink(missing_ok=True)
    except Exception:
        pass
