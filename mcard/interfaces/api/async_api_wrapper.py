"""API async wrapper for MCard operations."""
from typing import Optional, List
from datetime import datetime
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
from mcard.domain.models.protocols import CardStore

class AsyncAPIWrapper:
    """Asynchronous wrapper for MCard operations."""
    
    def __init__(self, store: CardStore):
        """Initialize the wrapper with a store that implements CardStore protocol."""
        self._store = store

    async def __aenter__(self):
        """Async context manager entry."""
        if hasattr(self._store, '__aenter__'):
            await self._store.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self._store, '__aexit__'):
            await self._store.__aexit__(exc_type, exc_val, exc_tb)

    async def save(self, card: MCard) -> None:
        """Save a card asynchronously."""
        await self._store.save(card)

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards asynchronously."""
        await self._store.save_many(cards)

    async def get(self, hash_value: str) -> Optional[MCard]:
        """Get a card by hash asynchronously."""
        return await self._store.get(hash_value)

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[MCard]:
        """List cards with optional filtering and pagination."""
        return await self._store.list(start_time, end_time, content, limit, offset)

    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        await self._store.remove(hash_str)
