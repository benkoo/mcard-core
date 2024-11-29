"""Test configuration loading from environment variables."""
import os
import asyncio
import logging
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient
import sqlite3
import dotenv
from pathlib import Path

# Import configuration and schema initialization
from mcard.domain.models.config import AppSettings
from mcard.domain.models.repository_config import SQLiteConfig, RepositoryType
from mcard.infrastructure.persistence.repository_factory import get_repository
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore

# Import the main API application
from mcard.interfaces.api.mcard_api import app, load_config

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
MCARD_MANAGER_REPOSITORY_TYPE=sqlite
MCARD_MANAGER_POOL_SIZE=3
MCARD_MANAGER_TIMEOUT=15.0
MCARD_MANAGER_MAX_CONTENT_SIZE=5242880
""")
        temp_env.flush()
        temp_path = temp_env.name
        
    yield temp_path
    os.unlink(temp_path)

@pytest.mark.asyncio
async def test_config_env_loading(temp_env_file):
    """Test configuration loading from environment variables."""
    # Load environment variables from temp file
    dotenv.load_dotenv(temp_env_file, override=True)
    
    # Verify environment variables are loaded
    assert os.getenv('MCARD_API_KEY') == 'test_custom_api_key_12345'
    assert os.getenv('MCARD_MANAGER_DB_PATH') == 'test_custom_database.db'
    
    # Load configuration
    config = load_config()
    assert isinstance(config.repository, SQLiteConfig)
    assert config.repository.db_path == 'test_custom_database.db'
    assert config.repository.type == RepositoryType.SQLITE
    assert config.mcard_api_key == 'test_custom_api_key_12345'