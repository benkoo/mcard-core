"""Setup script for MCard JavaScript bridge."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

import json
from mcard.infrastructure.setup import MCardSetup
from mcard.domain.models.config import AppSettings
from mcard.config_constants import (
    ENV_DB_PATH,
    ENV_API_PORT,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    DEFAULT_API_PORT
)
import asyncio

async def get_setup_config():
    """Get setup configuration using MCardSetup."""
    # Ensure data directory exists
    data_dir = Path('./data')
    data_dir.mkdir(exist_ok=True)

    # Initialize MCardSetup with environment variables
    setup = MCardSetup(
        db_path=os.getenv(ENV_DB_PATH, './data/mcard.db'),
        max_connections=int(os.getenv(ENV_DB_MAX_CONNECTIONS, '5')),
        timeout=float(os.getenv(ENV_DB_TIMEOUT, '5.0'))
    )

    # Initialize database
    await setup.initialize()

    # Create configuration for JavaScript client
    config = {
        'port': int(os.getenv(ENV_API_PORT, str(DEFAULT_API_PORT))),
        'api_key': os.getenv('MCARD_API_KEY', 'default_key')
    }

    # Output configuration as JSON
    print(json.dumps(config))

if __name__ == '__main__':
    asyncio.run(get_setup_config())
