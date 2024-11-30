"""Base class for async SQLite operations."""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.engine_config import SQLiteConfig

class AsyncSQLiteBase(ABC):
    """Base class for async SQLite operations."""

    def __init__(self, config: SQLiteConfig):
        """Initialize with configuration."""
        self._config = config
        self._connection = None

    @abstractmethod
    async def _initialize_connection(self):
        """Initialize the database connection."""
        pass

    @abstractmethod
    async def _close_connection(self):
        """Close the database connection."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_connection()

    async def close(self):
        """Close the connection explicitly."""
        await self._close_connection()

    def _check_connection(self):
        """Verify connection is initialized."""
        if not self._connection:
            raise StorageError("Database connection not initialized")
        return self._connection

    @abstractmethod
    async def get(self, hash_str: str) -> Optional[MCard]:
        """Get a card by its hash."""
        pass

    @abstractmethod
    async def save(self, card: MCard) -> None:
        """Save a card."""
        pass

    @abstractmethod
    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards."""
        pass

    @abstractmethod
    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[MCard]:
        """List cards with optional filtering and pagination."""
        pass
