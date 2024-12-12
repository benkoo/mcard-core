"""
Database Facade that provides a unified interface for database operations.
This facade abstracts away the specific database implementation details.
"""

from typing import Optional, List, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.database_engine_config import EngineConfig, EngineType, SQLiteConfig, DatabaseType
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.persistence.schema import SchemaManager


@dataclass
class DatabaseConfig:
    """Configuration for database connection."""
    engine_config: EngineConfig
    # Add more common configuration parameters as needed
    pragmas: Optional[dict] = None
    pool_size: Optional[int] = None
    timeout: Optional[float] = None


class DatabaseFactory:
    """Factory for creating database stores."""
    
    @staticmethod
    def create_store(config: DatabaseConfig) -> CardStore:
        """Create a store instance based on the configuration."""
        if config.engine_config.engine_type == EngineType.SQLITE:
            # Update SQLiteConfig with additional options from DatabaseConfig
            sqlite_config = SQLiteConfig(
                db_path=config.engine_config.connection_string,
                max_connections=config.pool_size or config.engine_config.max_connections,
                timeout=config.timeout or config.engine_config.timeout,
                check_same_thread=config.engine_config.engine_options.get('check_same_thread', False),
                max_content_size=config.engine_config.max_content_size
            )
            return SQLiteStore(sqlite_config)
        # Add more database implementations as needed
        raise ValueError(f"Unsupported database type: {config.engine_config.engine_type}")


class DatabaseFacade:
    """
    Facade for database operations.
    Provides a simplified interface for database operations while hiding the complexity
    of specific database implementations.
    """
    
    def __init__(self, config: DatabaseConfig):
        """Initialize the facade with database configuration."""
        self._config = config
        self._store = DatabaseFactory.create_store(config)
        self._schema_manager = SchemaManager()

    async def save_card(self, card: MCard) -> None:
        """Save a card to the database."""
        await self._store.save(card)

    async def get_card(self, card_id: str) -> Optional[MCard]:
        """Retrieve a card by its ID."""
        return await self._store.get(card_id)

    async def delete_card(self, card_id: str) -> None:
        """Delete a card by its ID."""
        await self._store.delete(card_id)

    async def list_cards(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List cards with optional pagination."""
        return await self._store.list(limit=limit, offset=offset)

    async def search_cards(self, query: str) -> List[MCard]:
        """Search for cards based on a query."""
        return await self._store.search(query)

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards in a batch."""
        await self._store.save_many(cards)

    async def save_many_cards(self, cards: List[MCard]) -> None:
        """Save multiple cards in a batch operation."""
        if not self._store:
            raise StorageError("Database engine not initialized")
        
        await self._store.save_many(cards)

    async def close(self) -> None:
        """Close the database connection."""
        await self._store.close()

    async def initialize_schema(self) -> None:
        """Initialize the database schema."""
        # Ensure the store is initialized first
        if hasattr(self._store, 'initialize'):
            await self._store.initialize()

        # Ensure tables are defined
        if not hasattr(self._schema_manager, '_tables') or self._schema_manager._tables is None:
            self._schema_manager._tables = self._schema_manager._define_tables()

        # Now check for connection
        if hasattr(self._store, '_connection') and self._store._connection is not None:
            schema_handler = self._schema_manager.get_schema_handler(self._config.engine_config.engine_type)
            await schema_handler.initialize_schema(self._store._connection, self._schema_manager._tables)
        else:
            raise StorageError("Database connection not established")

    @property
    def store(self) -> CardStore:
        """Get the underlying store instance."""
        return self._store
