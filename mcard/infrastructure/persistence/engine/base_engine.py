"""Base store implementation."""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore


class BaseStore(CardStore, ABC):
    """Base store implementation."""

    @abstractmethod
    async def initialize(self):
        """Initialize the store."""
        pass

    @abstractmethod
    async def close(self):
        """Close the store."""
        pass

    @abstractmethod
    async def create(self, content: str) -> MCard:
        """Create a new card with the given content."""
        pass

    @abstractmethod
    async def create_many(self, contents: List[str]) -> List[MCard]:
        """Create multiple cards with the given contents."""
        pass

    @abstractmethod
    async def get(self, hash_str: str) -> Optional[MCard]:
        """Get a card by its hash."""
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

    @abstractmethod
    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        pass

    async def __aenter__(self):
        """Async context manager entry point."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.close()
