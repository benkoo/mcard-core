import os
from dotenv import load_dotenv
from mcard.interfaces.api.app import create_card, get_card, CardCreate, CardResponse
from mcard.domain.models.config import AppSettings, DatabaseSettings, HashingSettings

# Load environment variables
load_dotenv('.env.mcard_manager')

# Load application settings from environment
app_settings = AppSettings(
    database=DatabaseSettings(
        db_path=os.getenv('MCARD_MANAGER_DB_PATH', 'MCardManagerStore.db'),
        data_source=os.getenv('MCARD_MANAGER_DATA_SOURCE'),
        pool_size=int(os.getenv('MCARD_MANAGER_POOL_SIZE', 5)),
        timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', 30.0))
    ),
    hashing=HashingSettings(
        algorithm=os.getenv('MCARD_MANAGER_HASH_ALGORITHM', 'sha256'),
        custom_module=os.getenv('MCARD_MANAGER_CUSTOM_MODULE'),
        custom_function=os.getenv('MCARD_MANAGER_CUSTOM_FUNCTION'),
        custom_hash_length=int(os.getenv('MCARD_MANAGER_CUSTOM_HASH_LENGTH', 0))
    )
)

class MCardStorageService:
    def __init__(self):
        self.settings = app_settings

    def store_mcard(self, content: str) -> CardResponse:
        """Store a new MCard using the API."""
        card_create = CardCreate(content=content)
        return create_card(card_create)

    def load_mcard(self, hash_str: str) -> CardResponse:
        """Load an MCard using the API by its hash."""
        return get_card(hash_str)