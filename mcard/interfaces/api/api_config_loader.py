"""Configuration management for MCard API."""
import os
from pathlib import Path
from dotenv import load_dotenv
from mcard.domain.models.domain_config_models import AppSettings, DatabaseSettings, HashingSettings
from mcard.config_constants import (
    ENV_DB_PATH,
    ENV_API_PORT,
    ENV_SERVICE_LOG_LEVEL,
    DEFAULT_API_PORT,
    DEFAULT_API_KEY
)

def load_environment():
    """Load environment variables from .env file."""
    if os.getenv('TESTING') == 'true':
        test_env_path = Path(__file__).parent.parent.parent.parent / 'tests' / '.env.test'
        load_dotenv(test_env_path, override=True)
    else:
        load_dotenv()

def load_config():
    """Load application settings from environment variables."""
    load_environment()
    
    return AppSettings(
        database=DatabaseSettings(
            db_path=os.getenv(ENV_DB_PATH, 'MCardManagerStore.db'),
            max_connections=int(os.getenv('MCARD_MANAGER_POOL_SIZE', '5')),
            timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', '30.0')),
            data_source='sqlite'
        ),
        hashing=HashingSettings(
            algorithm=os.getenv('MCARD_MANAGER_HASH_ALGORITHM', 'sha256'),
            custom_module=os.getenv('MCARD_MANAGER_CUSTOM_MODULE'),
            custom_function=os.getenv('MCARD_MANAGER_CUSTOM_FUNCTION'),
            custom_hash_length=int(os.getenv('MCARD_MANAGER_CUSTOM_HASH_LENGTH', '0'))
        ),
        mcard_api_key=os.getenv('MCARD_API_KEY', DEFAULT_API_KEY),
        mcard_api_port=int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT))
    )
