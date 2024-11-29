"""
MCardStore singleton class that provides a unified interface for all persistence operations.
This class follows the Singleton pattern to ensure a single instance is shared across the application.
"""

import os
from typing import Optional, List, Dict, Any
from threading import Lock
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.facade import DatabaseFacade, DatabaseConfig
from mcard.infrastructure.persistence.engine_config import EngineConfig, EngineType, create_engine_config
from mcard.domain.dependency.hashing import HashingService
from mcard.infrastructure.config import load_config

class MCardStore:
    """
    Singleton class for managing all persistence operations.
    This class provides a unified interface for storing and retrieving cards,
    while abstracting away the specific database implementation details.
    """
    _instance = None
    _lock = Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the store if not already initialized."""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._facade = None
                    self._config = None
                    self._hashing_service = None
                    self._initialized = True

    def configure(self, 
                 engine_type: EngineType = EngineType.SQLITE,
                 connection_string: Optional[str] = None,
                 **kwargs) -> None:
        """
        Configure the store with specific database settings.
        
        Args:
            engine_type: Type of database engine to use (SQLite, PostgreSQL, etc.)
            connection_string: Connection string or path for the database
            **kwargs: Additional database-specific configuration options
        """
        if self._facade is not None:
            raise RuntimeError("Store is already configured. Call reset() first to reconfigure.")

        # Load configuration including hashing settings
        config = load_config()

        # Set default SQLite path if none provided
        if engine_type == EngineType.SQLITE and not connection_string:
            connection_string = os.path.expanduser("~/.mcard/storage.db")
            os.makedirs(os.path.dirname(connection_string), exist_ok=True)

        # Create engine config
        engine_config = create_engine_config(
            engine_type=engine_type,
            connection_string=connection_string,
            **kwargs
        )

        # Create database config
        self._config = DatabaseConfig(
            engine_config=engine_config,
            pragmas=kwargs.get('pragmas'),
            pool_size=kwargs.get('pool_size'),
            timeout=kwargs.get('timeout')
        )

        # Initialize hashing service
        self._hashing_service = HashingService(config.hashing)

        # Initialize the facade
        self._facade = DatabaseFacade(self._config)

    async def initialize(self) -> None:
        """Initialize the database schema and ensure the store is ready for use."""
        if self._facade is None:
            self.configure()  # Use defaults if not configured
        await self._facade.initialize_schema()

    def compute_hash(self, content: bytes) -> str:
        """Compute hash for content using configured hash algorithm."""
        if self._hashing_service is None:
            config = load_config()
            self._hashing_service = HashingService(config.hashing)
        return self._hashing_service.hash_content(content)

    async def save(self, card: MCard) -> None:
        """Save a card to the store."""
        if not self._facade:
            raise StorageError("Store not configured")
        
        if card.hash is None:
            card.hash = self.compute_hash(card.content.encode('utf-8'))
        await self._facade.save_card(card)

    async def get(self, card_id: str) -> Optional[MCard]:
        """Retrieve a card by its ID."""
        if not self._facade:
            raise StorageError("Store not configured")
        return await self._facade.get_card(card_id)

    async def delete(self, card_id: str) -> None:
        """Delete a card by its ID."""
        if not self._facade:
            raise StorageError("Store not configured")
        await self._facade.delete_card(card_id)

    async def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List cards with optional pagination."""
        if not self._facade:
            raise StorageError("Store not configured")
        return await self._facade.list_cards(limit=limit, offset=offset)

    async def search(self, query: str) -> List[MCard]:
        """Search for cards based on a query."""
        if not self._facade:
            raise StorageError("Store not configured")
        return await self._facade.search_cards(query)

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards in a batch."""
        if not self._facade:
            raise StorageError("Store not configured")
        
        # Compute hashes for cards that don't have them
        for card in cards:
            if card.hash is None:
                card.hash = self.compute_hash(card.content.encode('utf-8'))
        await self._facade.save_many_cards(cards)

    async def close(self) -> None:
        """Close the database connection."""
        if self._facade:
            await self._facade.close()

    async def reset(self) -> None:
        """Reset the store configuration. Useful for testing."""
        if self._facade:
            await self._facade.close()
        self._facade = None
        self._config = None
        self._hashing_service = None

    @property
    def is_configured(self) -> bool:
        """Check if the store is configured."""
        return self._facade is not None

    @property
    def config(self) -> Optional[DatabaseConfig]:
        """Get the current database configuration."""
        return self._config
