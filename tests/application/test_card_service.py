"""Tests for CardService."""
import pytest
from typing import Any, Dict, List, Optional
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardRepository, ContentTypeService
from mcard.domain.models.exceptions import ValidationError
from mcard.application.card_service import CardService

class MockCardRepository:
    """Mock implementation of CardRepository."""
    def __init__(self):
        self.cards: Dict[str, MCard] = {}

    async def save(self, card: MCard) -> None:
        """Save a card."""
        self.cards[card.hash] = card

    async def get(self, hash: str) -> Optional[MCard]:
        """Get a card by hash."""
        return self.cards.get(hash)

    async def get_all(self) -> List[MCard]:
        """Get all cards."""
        return list(self.cards.values())

    async def delete(self, hash: str) -> None:
        """Delete a card by hash."""
        if hash in self.cards:
            del self.cards[hash]

class MockContentTypeService:
    """Mock implementation of ContentTypeService."""
    def __init__(self, valid_types: List[Any]):
        self.valid_types = valid_types

    def validate_content(self, content: Any) -> bool:
        """Validate content type."""
        return type(content) in self.valid_types

    def detect_type(self, content: Any) -> str:
        """Detect content type."""
        return content.__class__.__name__

@pytest.fixture
def repository():
    """Fixture for mock repository."""
    return MockCardRepository()

@pytest.fixture
def content_service():
    """Fixture for mock content service."""
    return MockContentTypeService([str, bytes, dict])

@pytest.fixture
def card_service(repository, content_service):
    """Fixture for card service."""
    return CardService(repository, content_service)

@pytest.mark.asyncio
async def test_create_card_with_valid_content(card_service):
    """Test creating a card with valid content."""
    content = "test content"
    card = await card_service.create_card(content)
    assert card.content == content
    assert card.hash is not None

@pytest.mark.asyncio
async def test_create_card_with_invalid_content(card_service):
    """Test creating a card with invalid content type."""
    content = 12345  # int is not in valid_types
    with pytest.raises(ValidationError, match="Invalid content type"):
        await card_service.create_card(content)

@pytest.mark.asyncio
async def test_get_card(card_service):
    """Test retrieving a card by hash."""
    # First create a card
    content = "test content"
    card = await card_service.create_card(content)
    
    # Then retrieve it
    retrieved_card = await card_service.get_card(card.hash)
    assert retrieved_card is not None
    assert retrieved_card.content == content
    assert retrieved_card.hash == card.hash

@pytest.mark.asyncio
async def test_get_nonexistent_card(card_service):
    """Test retrieving a non-existent card."""
    card = await card_service.get_card("nonexistent_hash")
    assert card is None

@pytest.mark.asyncio
async def test_get_all_cards(card_service):
    """Test retrieving all cards."""
    # Create multiple cards
    contents = ["content1", "content2", "content3"]
    created_cards = []
    for content in contents:
        card = await card_service.create_card(content)
        created_cards.append(card)

    # Retrieve all cards
    all_cards = await card_service.get_all_cards()
    assert len(all_cards) == len(contents)
    for card in created_cards:
        assert card in all_cards

@pytest.mark.asyncio
async def test_delete_card(card_service):
    """Test deleting a card."""
    # First create a card
    content = "test content"
    card = await card_service.create_card(content)
    
    # Then delete it
    await card_service.delete_card(card.hash)
    
    # Verify it's deleted
    retrieved_card = await card_service.get_card(card.hash)
    assert retrieved_card is None

@pytest.mark.asyncio
async def test_delete_nonexistent_card(card_service):
    """Test deleting a non-existent card."""
    # Should not raise any error
    await card_service.delete_card("nonexistent_hash")

def test_get_content_type(card_service):
    """Test getting content type."""
    test_cases = [
        ("test string", "str"),
        (b"test bytes", "bytes"),
        ({"key": "value"}, "dict")
    ]
    
    for content, expected_type in test_cases:
        assert card_service.get_content_type(content) == expected_type

@pytest.mark.asyncio
async def test_create_multiple_cards_same_content(card_service):
    """Test creating multiple cards with the same content."""
    content = "test content"
    card1 = await card_service.create_card(content)
    card2 = await card_service.create_card(content)
    
    # Cards should have same content but different timestamps
    assert card1.content == card2.content
    assert card1.hash == card2.hash  # Hash should be same for same content
    assert card1.g_time != card2.g_time
