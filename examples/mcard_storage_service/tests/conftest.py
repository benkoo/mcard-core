import os
import sys
import pytest
import tempfile
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from dotenv import load_dotenv

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load test environment variables
load_dotenv("tests/.env.test")

# Import our FastAPI app
from mcard_storage_service import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database file for testing."""
    # Use the database path from the environment variable if set
    db_path = os.getenv("MCARD_MANAGER_DB_PATH")
    if not db_path:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        os.environ["MCARD_MANAGER_DB_PATH"] = db_path
    
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture
def test_client(test_db_path) -> Generator[TestClient, None, None]:
    """Create a test client for synchronous tests."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def async_client(test_db_path) -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for asynchronous tests."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.fixture
def auth_headers() -> dict:
    """Return authentication headers for testing."""
    return {"x-api-key": os.getenv("MCARD_API_KEY", "test_api_key_12345")}
