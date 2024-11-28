import logging
import sqlite3
import os
from mcard.infrastructure.persistence.schema_utils import initialize_schema
from mcard.domain.models.protocols import CardRepository
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.domain.models.config import AppSettings, DatabaseSettings

class SchemaInitializer:
    """
    Single Source of Truth (SSOT) for initializing the database schema.

    This class is responsible for ensuring that the database schema is created consistently across
    different repository implementations. It encapsulates the schema creation logic to maintain a
    single source of truth, reducing redundancy and potential errors.
    """

    @staticmethod
    def initialize_schema(connection: sqlite3.Connection):
        """
        Initialize the database schema.

        This method creates the necessary tables with the specified schema. The `g_time` column is
        a string representing the global time when the card was claimed, with microsecond precision.
        The `hash` column is a cryptographic hash computed from the card content.
        """
        logging.debug("Initializing database schema.")
        initialize_schema(connection)
        logging.debug("Database schema initialized.")

# Global variable to hold the shared repository instance
_shared_repository_instance = None

async def get_repository() -> CardRepository:
    """Get a repository instance."""
    global _shared_repository_instance
    if _shared_repository_instance is None:
        app_settings = AppSettings(
            database=DatabaseSettings(
                db_path=os.getenv('MCARD_MANAGER_DB_PATH', 'MCardManagerStore.db'),
                data_source=os.getenv('MCARD_MANAGER_DATA_SOURCE'),
                pool_size=int(os.getenv('MCARD_MANAGER_POOL_SIZE', 5)),
                timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', 30.0))
            ),
            mcard_api_key=os.getenv('MCARD_API_KEY', 'test_api_key')
        )
        _shared_repository_instance = SQLiteRepository(db_path=app_settings.database.db_path)
    return _shared_repository_instance
