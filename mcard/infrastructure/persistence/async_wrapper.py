"""Async wrapper for SQLite store."""
from typing import List, Optional
from datetime import datetime
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore, SQLiteConfig


class AsyncSQLiteWrapper(CardStore):
    """Async wrapper for SQLite store."""

    def __init__(self, store_or_config):
        """Initialize AsyncSQLiteWrapper with a store or config."""
        if isinstance(store_or_config, SQLiteConfig):
            self.store = SQLiteStore(store_or_config)
        else:
            self.store = store_or_config

    async def create(self, content: str) -> MCard:
        """Create a new card with the given content."""
        return await self.store.create(content)

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Get a card by its hash."""
        return await self.store.get(hash_str)

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[MCard]:
        """List cards with optional filtering and pagination."""
        return await self.store.list(start_time, end_time, content, limit, offset)

    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        await self.store.remove(hash_str)

    async def __aenter__(self):
        """Async context manager entry point."""
        if hasattr(self.store, 'initialize'):
            await self.store.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        if hasattr(self.store, 'close'):
            await self.store.close()

    async def close(self):
        """Close the underlying store."""
        if hasattr(self.store, 'close'):
            await self.store.close()