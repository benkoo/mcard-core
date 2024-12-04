"""Async wrapper for persistence store."""
from typing import List, Optional
from datetime import datetime
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore
from mcard.infrastructure.persistence.engine.base_engine import BaseStore
from mcard.infrastructure.persistence.engine_config import EngineConfig


class AsyncPersistenceWrapper(CardStore):
    """Async wrapper for persistence store."""

    def __init__(self, store_or_config):
        """Initialize AsyncPersistenceWrapper with a store or config."""
        if isinstance(store_or_config, EngineConfig):
            self.store = store_or_config.create_store()
        else:
            self.store = store_or_config

    async def initialize(self):
        """Initialize the store."""
        if hasattr(self.store, 'initialize'):
            await self.store.initialize()

    async def close(self):
        """Close the store."""
        if hasattr(self.store, 'close'):
            await self.store.close()

    async def save(self, card: MCard) -> None:
        """Save a card."""
        await self.store.save(card)

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards."""
        for card in cards:
            await self.store.save(card)

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

    async def create(self, content: str) -> MCard:
        """Create a new card with the given content."""
        return await self.store.create(content)

    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        await self.store.remove(hash_str)

    async def __aenter__(self):
        """Async context manager entry point."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.close()
