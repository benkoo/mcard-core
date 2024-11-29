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
from mcard.infrastructure.persistence.schema import SQLiteSchemaHandler
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
MCARD_STORE_DB_PATH=data/test_custom_database.db
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
    print(f"MCARD_STORE_DB_PATH: {os.getenv('MCARD_STORE_DB_PATH')}")
    
    # Reload the app settings to ensure they reflect the latest environment variables
    loaded_app_settings = load_app_settings()
    
    yield temp_env.name
    
    # Clean up: remove the temporary file and reset environment
    try:
        os.unlink(temp_env.name)
    except OSError:
        pass

@pytest_asyncio.fixture
async def app_settings():
    """Load application settings from the temporary .env file."""
    return load_app_settings()

@pytest_asyncio.fixture
async def async_client():
    """Create an async client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def initialized_database(app_settings):
    """Initialize the database for testing."""
    db_path = app_settings.database.db_path
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize database schema
    conn = sqlite3.connect(db_path)
    schema_handler = SQLiteSchemaHandler()
    tables = {
        'card': TableDefinition(
            name='card',
            columns=[
                ColumnDefinition(name='id', type=ColumnType.TEXT, primary_key=True),
                ColumnDefinition(name='content', type=ColumnType.BLOB),
                ColumnDefinition(name='created_at', type=ColumnType.TIMESTAMP),
                ColumnDefinition(name='updated_at', type=ColumnType.TIMESTAMP),
            ]
        )
    }
    schema_handler.initialize_schema(conn, tables)
    conn.close()
    
    return db_path

@pytest.fixture
def custom_api_key(app_settings):
    """Return the custom API key from settings."""
    return app_settings.mcard_api_key

@pytest.fixture
def test_content():
    """Provide a test content for card creation."""
    return {"content": "Configuration Test Card"}

@pytest.mark.asyncio
async def test_config_env_loading(
    temp_env_file, 
    app_settings, 
    async_client, 
    initialized_database, 
    custom_api_key, 
    test_content
):
    """
    Test configuration loading from a custom .env file:
    1. Verify that custom API key is loaded correctly
    2. Verify that custom database path is used
    3. Test API authentication with custom key
    4. Verify database creation at custom path
    """
    # Verify custom API key is loaded
    assert app_settings.mcard_api_key == custom_api_key
    
    # Verify custom database path is used
    expected_db_path = "data/test_custom_database.db"
    assert app_settings.database.db_path == expected_db_path
    
    # Test API authentication with custom key
    headers = {"X-API-Key": custom_api_key}
    async with async_client as client:
        response = await client.post("/api/v1/cards", json=test_content, headers=headers)
        assert response.status_code == 200
        
        # Verify card was created
        card_id = response.json()["id"]
        response = await client.get(f"/api/v1/cards/{card_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["content"] == test_content["content"]
    
    # Verify database was created at custom path
    db_path = app_settings.database.db_path
    assert os.path.exists(db_path)
    
    # Clean up database file
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass

if __name__ == "__main__":
    # Use pytest to run the async test
    pytest.main([__file__])
