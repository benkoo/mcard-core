"""Test MCard config environment."""
import os
import pytest
import logging
import tempfile
from pathlib import Path
from mcard.domain.models.domain_config_models import AppSettings, DatabaseSettings, HashingSettings

# Import repository configuration and schema initialization
from mcard.domain.models.repository_config_models import SQLiteConfig, RepositoryType

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
MCARD_MANAGER_HASH_ALGORITHM=sha256
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
    
    # Create AppSettings from environment
    config = AppSettings(
        database=DatabaseSettings(
            db_path=os.getenv('MCARD_MANAGER_DB_PATH'),
            max_connections=int(os.getenv('MCARD_MANAGER_POOL_SIZE', '3')),
            timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', '15.0')),
            data_source=os.getenv('MCARD_MANAGER_REPOSITORY_TYPE', 'sqlite')
        ),
        hashing=HashingSettings(
            algorithm=os.getenv('MCARD_MANAGER_HASH_ALGORITHM', 'sha256')
        ),
        mcard_api_key=os.getenv('MCARD_API_KEY'),
        mcard_api_port=int(os.getenv('MCARD_API_PORT', '8888'))
    )
    
    # Verify configuration
    assert config.database.db_path == 'test_custom_database.db'
    assert config.database.data_source == 'sqlite'
    assert config.database.max_connections == 3
    assert config.database.timeout == 15.0
    assert config.mcard_api_key == 'test_custom_api_key_12345'
    assert config.mcard_api_port == 8888
    assert config.hashing.algorithm == 'sha256'
