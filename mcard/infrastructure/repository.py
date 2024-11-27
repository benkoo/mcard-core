"""
Repository implementation for MCard.
"""
from typing import Optional, List
from datetime import datetime

from ..domain.models.card import MCard
from ..domain.models.protocols import CardRepository

class InMemoryRepository(CardRepository):
    """In-memory implementation of CardRepository for testing."""
    def __init__(self):
        self.cards = {}

    async def save(self, card: MCard) -> None:
        """Save a card to the repository."""
        self.cards[card.hash] = card

    async def save_many(self, cards: list[MCard]) -> None:
        """Save multiple cards to the repository."""
        for card in cards:
            await self.save(card)

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        return self.cards.get(hash_str)

    async def get_many(self, hash_strs: list[str]) -> list[MCard]:
        """Retrieve multiple cards by their hashes."""
        return [self.cards[h] for h in hash_strs if h in self.cards]

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[MCard]:
        """Retrieve all cards with optional pagination."""
        cards = list(self.cards.values())
        if offset is not None:
            cards = cards[offset:]
        if limit is not None:
            cards = cards[:limit]
        return cards

    async def get_by_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[MCard]:
        """Retrieve cards within a time range."""
        cards = list(self.cards.values())
        if start_time:
            cards = [c for c in cards if c.g_time >= start_time]
        if end_time:
            cards = [c for c in cards if c.g_time <= end_time]
        if offset is not None:
            cards = cards[offset:]
        if limit is not None:
            cards = cards[:limit]
        return cards

async def get_repository() -> CardRepository:
    """Get a repository instance."""
    return InMemoryRepository()
