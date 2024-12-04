"""
Concrete implementations of repository protocols.
"""
from typing import Optional, List
from datetime import datetime

from ...domain.models.card import MCard
from ...domain.models.protocols import CardStore
from ...domain.models.config import SQLiteConfig
from .engine.sqlite_engine import SQLiteStore

class SQLiteCardRepo(CardStore):
    """
    SQLite implementation of the CardStore protocol.
    """
    def __init__(self, db_path: str, pool_size: int = 5):
        """
        Initialize the SQLite card repository.
        
        Args:
            db_path: Path to the SQLite database
            pool_size: Connection pool size
        """
        config = SQLiteConfig(
            db_path=db_path,
            pool_size=pool_size
        )
        self._store = SQLiteStore(config)

    async def save(self, card: MCard) -> None:
        """Save a single card."""
        await self._store.save(card)

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards."""
        await self._store.save_many(cards)

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        return await self._store.get(hash_str)

    async def get_many(self, hash_strs: List[str]) -> List[MCard]:
        """Retrieve multiple cards by their hashes."""
        return await self._store.get_many(hash_strs)

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Retrieve all cards with optional pagination."""
        return await self._store.get_all(limit, offset)

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        """List cards within a time range with optional pagination."""
        return await self._store.list(start_time, end_time, limit, offset)

    async def delete(self, hash_str: str) -> None:
        """Delete a card by its hash."""
        await self._store.delete(hash_str)

    async def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards by their hashes."""
        await self._store.delete_many(hash_strs)

    async def close(self) -> None:
        """Close the repository connection."""
        await self._store.close()
