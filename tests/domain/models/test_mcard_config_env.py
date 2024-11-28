import os
import asyncio
import logging
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient
import sqlite3
import dotenv

# Import configuration and schema initialization
from mcard.domain.models.config import AppSettings, DatabaseSettings
from mcard.infrastructure.persistence.schema_initializer import SchemaInitializer, get_repository
from mcard.infrastructure.repository import SQLiteRepository

# Import the main API application
from mcard.interfaces.api.mcard_api import app, load_app_settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file with custom configuration."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as temp_env:
        # Write custom configuration
        temp_env.write("""
# Custom Test Configuration
MCARD_API_KEY=test_custom_api_key_12345
MCARD_API_PORT=8888
MCARD_MANAGER_DB_PATH=test_custom_database.db
MCARD_MANAGER_DATA_SOURCE=sqlite
MCARD_MANAGER_POOL_SIZE=3
MCARD_MANAGER_TIMEOUT=15.0
""")
        temp_env.flush()
        
        # Explicitly load the environment variables from the temp file
        dotenv.load_dotenv(temp_env.name, override=True)
        
        # Verify the environment variables are loaded
        print("Loaded Environment Variables:")
        print(f"MCARD_API_KEY: {os.getenv('MCARD_API_KEY')}")
        print(f"MCARD_MANAGER_DB_PATH: {os.getenv('MCARD_MANAGER_DB_PATH')}")
        
        # Create app settings
        app_settings = AppSettings(
            database=DatabaseSettings(
                db_path=os.getenv('MCARD_MANAGER_DB_PATH', 'test_custom_database.db'),
                data_source=os.getenv('MCARD_MANAGER_DATA_SOURCE', 'sqlite'),
                pool_size=int(os.getenv('MCARD_MANAGER_POOL_SIZE', 3)),
                timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', 15.0))
            ),
            mcard_api_key=os.getenv('MCARD_API_KEY', 'test_custom_api_key_12345')
        )
        
        # Override app settings
        app.dependency_overrides[load_app_settings] = lambda: app_settings
        
        yield temp_env.name
        
        # Clean up
        os.unlink(temp_env.name)
        app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_client():
    """Create an async client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def initialized_database(temp_env_file):
    """Initialize the database for testing."""
    # Get settings
    settings = load_app_settings()
    db_path = settings.database.db_path
    
    # Create database and schema
    conn = sqlite3.connect(db_path)
    SchemaInitializer.initialize_schema(conn)
    conn.close()
    
    yield db_path
    
    # Clean up
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def test_content():
    """Provide a test content for card creation."""
    return "Test content for MCard"

@pytest.mark.asyncio
async def test_config_env_loading(temp_env_file, async_client, initialized_database, test_content):
    """
    Test configuration loading from a custom .env file:
    1. Verify that custom API key is loaded correctly
    2. Verify that custom database path is used
    3. Test API authentication with custom key
    4. Verify database creation at custom path
    """
    # Verify environment variables are loaded correctly
    settings = load_app_settings()
    assert settings.mcard_api_key == 'test_custom_api_key_12345'
    assert settings.database.db_path == 'test_custom_database.db'
    assert settings.database.data_source == 'sqlite'
    assert settings.database.pool_size == 3
    assert settings.database.timeout == 15.0
    
    # Test API authentication with custom key
    response = await async_client.post(
        "/cards/",
        json={"content": test_content},
        headers={"x-api-key": settings.mcard_api_key}
    )
    assert response.status_code == 201
    assert "hash" in response.json()

    # Verify database creation at custom path
    assert os.path.exists(settings.database.db_path)
