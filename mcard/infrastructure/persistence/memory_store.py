"""In-memory card store implementation."""
from typing import Optional, List, Dict
from datetime import datetime

from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore

class MemoryCardStore(CardStore):
    """In-memory implementation of CardStore."""

    def __init__(self):
        """Initialize the memory store."""
        self._store: Dict[str, MCard] = {}

    async def save(self, card: MCard) -> None:
        """Save a card to the store."""
        self._store[card.hash] = card

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards to the store."""
        for card in cards:
            self._store[card.hash] = card

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash from the store."""
        return self._store.get(hash_str)

    async def get_many(self, hash_strs: List[str]) -> List[MCard]:
        """Retrieve multiple cards by their hashes from the store."""
        return [self._store[h] for h in hash_strs if h in self._store]

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Retrieve all cards from the store with optional pagination."""
        cards = list(self._store.values())
        if offset is not None:
            cards = cards[offset:]
        if limit is not None:
            cards = cards[:limit]
        return cards

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[MCard]:
        """List cards with optional time range and pagination."""
        cards = list(self._store.values())
        
        # Filter by time range if specified
        if start_time or end_time:
            filtered_cards = []
            for card in cards:
                card_time = datetime.fromisoformat(card.g_time)
                if start_time and card_time < start_time:
                    continue
                if end_time and card_time > end_time:
                    continue
                filtered_cards.append(card)
            cards = filtered_cards

        # Apply pagination
        if offset is not None:
            cards = cards[offset:]
        if limit is not None:
            cards = cards[:limit]
        return cards

    async def delete(self, hash_str: str) -> None:
        """Delete a card from the store."""
        if hash_str in self._store:
            del self._store[hash_str]

    async def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards from the store."""
        for hash_str in hash_strs:
            if hash_str in self._store:
                del self._store[hash_str]
