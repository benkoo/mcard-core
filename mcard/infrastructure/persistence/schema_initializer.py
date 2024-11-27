import logging
import sqlite3
from mcard.infrastructure.persistence.schema_utils import initialize_schema
from mcard.domain.models.protocols import CardRepository
from mcard.infrastructure.repository import SQLiteInMemoryRepository

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
        _shared_repository_instance = SQLiteInMemoryRepository()
    return _shared_repository_instance
