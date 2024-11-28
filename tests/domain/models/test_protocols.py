"""
Tests for MCard domain protocols.
"""
import pytest
from datetime import datetime, timedelta
from typing import Optional, List, Union, Any
from unittest.mock import Mock

from mcard.domain.models.protocols import HashingService, CardRepository, ContentTypeService
from mcard.domain.models.card import MCard

class MockHashingService:
    """Mock implementation of HashingService protocol."""
    async def hash_content(self, content: bytes) -> str:
        return "mock_hash"

    async def validate_hash(self, hash_str: str) -> bool:
        return hash_str == "mock_hash"

class MockCardRepository:
    """Mock implementation of CardRepository protocol."""
    def __init__(self):
        self.cards = {}  # hash -> card mapping

    async def save(self, card: MCard) -> None:
        self.cards[card.hash] = card

    async def save_many(self, cards: List[MCard]) -> None:
        for card in cards:
            self.cards[card.hash] = card

    async def get(self, hash_str: str) -> Optional[MCard]:
        return self.cards.get(hash_str)

    async def get_many(self, hash_strs: List[str]) -> List[MCard]:
        return [self.cards[h] for h in hash_strs if h in self.cards]

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        cards = list(self.cards.values())
        if offset:
            cards = cards[offset:]
        if limit:
            cards = cards[:limit]
        return cards

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        cards = list(self.cards.values())
        if start_time:
            cards = [c for c in cards if c.g_time >= start_time]
        if end_time:
            cards = [c for c in cards if c.g_time <= end_time]
        if offset:
            cards = cards[offset:]
        if limit:
            cards = cards[:limit]
        return cards

    async def get_by_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        cards = list(self.cards.values())
        if start_time:
            cards = [c for c in cards if c.g_time >= start_time]
        if end_time:
            cards = [c for c in cards if c.g_time <= end_time]
        if offset:
            cards = cards[offset:]
        if limit:
            cards = cards[:limit]
        return cards

    async def get_before_time(
        self,
        time: datetime,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        cards = [c for c in self.cards.values() if c.g_time < time]
        if offset:
            cards = cards[offset:]
        if limit:
            cards = cards[:limit]
        return cards

    async def get_after_time(
        self,
        time: datetime,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        cards = [c for c in self.cards.values() if c.g_time > time]
        if offset:
            cards = cards[offset:]
        if limit:
            cards = cards[:limit]
        return cards

    async def delete(self, hash_str: str) -> None:
        if hash_str in self.cards:
            del self.cards[hash_str]

    async def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards by their hashes."""
        for hash_str in hash_strs:
            if hash_str in self.cards:
                del self.cards[hash_str]

    async def delete_before_time(self, time: datetime) -> int:
        """Delete all cards created before the specified time."""
        to_delete = [h for h, c in self.cards.items() if c.g_time < time]
        for hash_str in to_delete:
            del self.cards[hash_str]
        return len(to_delete)

    async def begin_transaction(self) -> None:
        """Begin a new transaction."""
        pass

    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass

    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass

class MockContentTypeService:
    """Mock implementation of ContentTypeService protocol."""
    async def detect_type(self, content: Union[str, bytes]) -> str:
        return "text/plain"

    async def validate_content(self, content: Any) -> bool:
        return True

@pytest.mark.asyncio
async def test_hashing_service_protocol():
    """Test that HashingService protocol can be implemented."""
    service = MockHashingService()
    
    # Test protocol implementation
    assert isinstance(service, HashingService)
    
    # Test functionality
    content = b"test content"
    hash_str = await service.hash_content(content)
    assert isinstance(hash_str, str)
    assert await service.validate_hash(hash_str)

@pytest.mark.asyncio
async def test_card_repository_protocol():
    """Test that CardRepository protocol can be implemented."""
    repo = MockCardRepository()
    
    # Test protocol implementation
    assert isinstance(repo, CardRepository)
    
    # Create test cards
    now = datetime.now()
    card1 = Mock(hash="hash1", g_time=now)
    card2 = Mock(hash="hash2", g_time=now + timedelta(hours=1))
    
    # Test save and get
    await repo.save(card1)
    assert await repo.get("hash1") == card1
    
    # Test save_many and get_many
    await repo.save_many([card1, card2])
    cards = await repo.get_many(["hash1", "hash2"])
    assert len(cards) == 2
    assert cards[0].hash in ["hash1", "hash2"]
    
    # Test get_all with pagination
    all_cards = await repo.get_all(limit=1, offset=0)
    assert len(all_cards) == 1
    
    # Test time-based queries
    time_cards = await repo.get_by_time_range(
        start_time=now - timedelta(minutes=1),
        end_time=now + timedelta(hours=2)
    )
    assert len(time_cards) == 2
    
    before_cards = await repo.get_before_time(now + timedelta(hours=2))
    assert len(before_cards) == 2
    
    after_cards = await repo.get_after_time(now - timedelta(minutes=1))
    assert len(after_cards) == 2
    
    # Test delete operations
    await repo.delete("hash1")
    assert await repo.get("hash1") is None

    await repo.save_many([card1, card2])
    await repo.delete_many(["hash1", "hash2"])
    assert await repo.get("hash1") is None
    assert await repo.get("hash2") is None

    await repo.save_many([card1, card2])
    deleted_count = await repo.delete_before_time(now + timedelta(hours=2))
    assert deleted_count == 2
    assert await repo.get("hash1") is None

@pytest.mark.asyncio
async def test_content_type_service_protocol():
    """Test that ContentTypeService protocol can be implemented."""
    service = MockContentTypeService()
    
    # Test protocol implementation
    assert isinstance(service, ContentTypeService)
    
    # Test functionality
    content = "test content"
    assert await service.detect_type(content) == "text/plain"
    assert await service.validate_content(content) is True
