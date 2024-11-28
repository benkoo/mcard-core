"""Tests for CardService."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from mcard.domain.models.card import MCard
from mcard.application.card_service import CardService
from mcard.domain.models.exceptions import ValidationError
from mcard.infrastructure.repository import SQLiteRepository

@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repository = AsyncMock()
    repository.save = AsyncMock()
    repository.get = AsyncMock()
    repository.get_all = AsyncMock(return_value=[])
    repository.delete = AsyncMock()
    return repository

@pytest.fixture
def mock_content_service():
    """Create a mock content type service."""
    service = MagicMock()
    service.validate_content.return_value = True
    service.detect_type.return_value = "text/plain"
    return service

@pytest.fixture
def mock_hashing():
    """Create a mock hashing service."""
    service = AsyncMock()
    service.hash_content = AsyncMock(return_value="test_hash")
    return service

@pytest.fixture
def card_service(mock_repository, mock_content_service, mock_hashing, monkeypatch):
    """Create a CardService with mocked dependencies."""
    def mock_get_hashing_service():
        return mock_hashing
    # Patch both the domain and application imports
    monkeypatch.setattr(
        "mcard.application.card_service.get_hashing_service",
        mock_get_hashing_service
    )
    monkeypatch.setattr(
        "mcard.domain.services.hashing.get_hashing_service",
        mock_get_hashing_service
    )
    return CardService(mock_repository, mock_content_service)

@pytest.mark.asyncio
async def test_create_card(card_service, mock_repository):
    """Test creating a new card."""
    content = "test content"
    card = await card_service.create_card(content)
    
    assert isinstance(card, MCard)
    assert card.content == content
    assert card.hash == "test_hash"
    mock_repository.save.assert_called_once()

@pytest.mark.asyncio
async def test_create_card_with_invalid_content(card_service, mock_content_service):
    """Test creating a card with invalid content."""
    mock_content_service.validate_content.return_value = False
    with pytest.raises(ValidationError):
        await card_service.create_card("invalid content")

@pytest.mark.asyncio
async def test_update_card_content(card_service, mock_repository):
    """Test updating a card's content."""
    # Setup existing card
    old_card = MCard(content="old content", hash="old_hash")
    mock_repository.get.return_value = old_card
    
    # Update content
    new_content = "new content"
    updated_card = await card_service.update_card_content("old_hash", new_content)
    
    assert isinstance(updated_card, MCard)
    assert updated_card.content == new_content
    assert updated_card.hash == "test_hash"  # From mock_hashing_service
    
    # Verify repository calls
    mock_repository.save.assert_called_once()
    mock_repository.delete.assert_called_once_with("old_hash")

@pytest.mark.asyncio
async def test_update_nonexistent_card(card_service, mock_repository):
    """Test updating a card that doesn't exist."""
    mock_repository.get.return_value = None
    with pytest.raises(ValidationError, match="Card with hash .* not found"):
        await card_service.update_card_content("nonexistent", "new content")

@pytest.mark.asyncio
async def test_update_card_invalid_content(card_service, mock_content_service, mock_repository):
    """Test updating a card with invalid content."""
    mock_repository.get.return_value = MCard(content="old", hash="old_hash")
    mock_content_service.validate_content.return_value = False
    
    with pytest.raises(ValidationError):
        await card_service.update_card_content("old_hash", "invalid content")

@pytest.mark.asyncio
async def test_get_card(card_service, mock_repository):
    """Test retrieving a card."""
    expected_card = MCard(content="test", hash="test_hash")
    mock_repository.get.return_value = expected_card
    
    card = await card_service.get_card("test_hash")
    assert card == expected_card
    mock_repository.get.assert_called_once_with("test_hash")

@pytest.mark.asyncio
async def test_delete_card(card_service, mock_repository):
    """Test deleting a card."""
    await card_service.delete_card("test_hash")
    mock_repository.delete.assert_called_once_with("test_hash")

@pytest.mark.asyncio
async def test_get_all_cards(card_service, mock_repository):
    """Test retrieving all cards."""
    expected_cards = [
        MCard(content="test1", hash="hash1"),
        MCard(content="test2", hash="hash2")
    ]
    mock_repository.get_all.return_value = expected_cards
    
    cards = await card_service.get_all_cards()
    assert cards == expected_cards
    mock_repository.get_all.assert_called_once()
