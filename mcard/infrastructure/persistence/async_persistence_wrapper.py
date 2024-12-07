"""Async wrapper for persistence store."""
from typing import List, Optional, Dict, Tuple
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

    async def get_total_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        hash_search: Optional[str] = None,
        g_time_search: Optional[str] = None,
    ) -> int:
        """Get total count of cards with optional filtering.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            content: Optional content filter
            hash_search: Optional hash text search
            g_time_search: Optional g_time text search
            
        Returns:
            Total number of matching cards
        """
        return await self.store.get_total_count(
            start_time=start_time,
            end_time=end_time,
            content=content,
            hash_search=hash_search,
            g_time_search=g_time_search,
        )

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        hash_search: Optional[str] = None,
        g_time_search: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Tuple[List[MCard], Optional[Dict]]:
        """List cards with optional filtering and pagination.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            content: Optional content filter
            hash_search: Optional hash text search
            g_time_search: Optional g_time text search
            page: Optional page number (1-based)
            page_size: Optional page size
            
        Returns:
            Tuple of (list of cards, pagination info dict)
            Pagination info includes: total, page, page_size, total_pages, has_next, has_previous
        """
        return await self.store.list(
            start_time=start_time,
            end_time=end_time,
            content=content,
            hash_search=hash_search,
            g_time_search=g_time_search,
            page=page,
            page_size=page_size,
        )

    async def search(
        self,
        query: str,
        search_hash: bool = True,
        search_content: bool = True,
        search_time: bool = True,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Tuple[List[MCard], Optional[Dict]]:
        """Search cards by text in hash, content, and/or g_time fields.
        
        Args:
            query: Text to search for
            search_hash: Whether to search in hash field
            search_content: Whether to search in content field
            search_time: Whether to search in g_time field
            page: Optional page number (1-based)
            page_size: Optional page size
            
        Returns:
            Tuple of (list of cards, pagination info dict)
            Pagination info includes: total, page, page_size, total_pages, has_next, has_previous
        """
        return await self.store.search(
            query=query,
            search_hash=search_hash,
            search_content=search_content,
            search_time=search_time,
            page=page,
            page_size=page_size,
        )

    async def create(self, content: str) -> MCard:
        """Create a new card with the given content."""
        return await self.store.create(content)

    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        await self.store.remove(hash_str)

    async def delete(self, hash_str: str) -> None:
        """Delete a card by its hash."""
        await self.store.remove(hash_str)

    async def delete_all(self) -> None:
        """Delete all cards from the store."""
        await self.store.delete_all()

    async def __aenter__(self):
        """Async context manager entry point."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.close()
