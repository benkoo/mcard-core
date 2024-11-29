"""Card service implementation."""
from typing import Optional, List
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import HashingService, CardStore
from mcard.domain.services.hashing import get_hashing_service

class CardService:
    """Card service implementation."""
    
    def __init__(self, store: CardStore, hashing_service: HashingService):
        """Initialize card service."""
        self.store = store
        self.hashing_service = hashing_service

    async def save_card(self, content: str) -> str:
        """Save a card with the given content."""
        hash_str = await self.hashing_service.hash_content(content.encode())
        g_time = datetime.now(timezone.utc).isoformat()
        card = MCard(content=content, hash=hash_str, g_time=g_time)
        await self.store.save(card)
        return hash_str

    async def get_card(self, hash_str: str) -> Optional[MCard]:
        """Get a card by its hash."""
        return await self.store.get(hash_str)

    async def get_cards(self, content: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Get all cards, optionally filtered by content."""
        return await self.store.get_all(content=content, limit=limit, offset=offset)

    async def get_many_cards(self, hashes: List[str]) -> List[MCard]:
        """Get multiple cards by their hashes."""
        return await self.store.get_many(hashes)

    async def save_many_cards(self, contents: List[str]) -> List[str]:
        """Save multiple cards."""
        cards = []
        hashes = []
        now = datetime.now(timezone.utc).isoformat()
        
        for content in contents:
            hash_str = await self.hashing_service.hash_content(content.encode())
            card = MCard(content=content, hash=hash_str, g_time=now)
            cards.append(card)
            hashes.append(hash_str)
        
        await self.store.save_many(cards)
        return hashes

    async def delete_card(self, hash_str: str) -> None:
        """Delete a card by its hash."""
        await self.store.delete(hash_str)

    async def close(self) -> None:
        """Close the service and its dependencies."""
        await self.store.close()

def get_hashing_service() -> HashingService:
    """Get the default hashing service."""
    return get_hashing_service()
