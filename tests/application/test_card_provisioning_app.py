"""Tests for CardProvisioningApp."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from mcard.domain.models.card import MCard
from mcard.application.card_provisioning_app import CardProvisioningApp
from mcard.domain.models.exceptions import ValidationError
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from datetime import datetime
import json


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
    service.next_level_hash = AsyncMock(return_value="stronger_hash")
    return service


@pytest.fixture
def provisioning_app(mock_repository, mock_content_service, mock_hashing, monkeypatch):
    """Create a CardProvisioningApp with mocked dependencies."""
    def mock_get_hashing_service():
        return mock_hashing
    # Patch both the domain and application imports
    monkeypatch.setattr(
        "mcard.application.card_provisioning_app.get_hashing_service",
        mock_get_hashing_service
    )
    monkeypatch.setattr(
        "mcard.domain.services.hashing.get_hashing_service",
        mock_get_hashing_service
    )
    return CardProvisioningApp(mock_repository, mock_content_service)


@pytest.mark.asyncio
async def test_create_card(provisioning_app, mock_repository):
    """Test creating a new card."""
    content = "test content"
    card = await provisioning_app.create_card(content)
    assert isinstance(card, MCard)
    mock_repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_card_with_invalid_content(provisioning_app, mock_content_service):
    """Test creating a card with invalid content."""
    mock_content_service.validate_content.return_value = False
    with pytest.raises(ValidationError):
        await provisioning_app.create_card("invalid content")


@pytest.mark.asyncio
async def test_update_card_content(provisioning_app, mock_repository):
    """Test updating a card's content."""
    old_hash = "old_hash"
    new_content = "new content"
    old_card = MCard(content="old content")
    updated_card = MCard(content=new_content)

    mock_repository.get.return_value = old_card
    mock_repository.save.return_value = updated_card

    updated_card = await provisioning_app.update_card_content(old_hash, new_content)
    assert isinstance(updated_card, MCard)
    mock_repository.get.assert_called_once_with(old_hash)
    mock_repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_card(provisioning_app, mock_repository):
    """Test updating a card that doesn't exist."""
    mock_repository.get.return_value = None
    with pytest.raises(ValidationError):
        await provisioning_app.update_card_content("nonexistent", "new content")


@pytest.mark.asyncio
async def test_update_card_invalid_content(provisioning_app, mock_content_service, mock_repository):
    """Test updating a card with invalid content."""
    mock_content_service.validate_content.return_value = False
    mock_repository.get.return_value = MCard(content="old content")

    with pytest.raises(ValidationError):
        await provisioning_app.update_card_content("old_hash", "invalid content")


@pytest.mark.asyncio
async def test_get_card(provisioning_app, mock_repository):
    """Test retrieving a card by hash."""
    test_hash = "test_hash"
    test_card = MCard(content="test")
    mock_repository.get.return_value = test_card
    
    card = await provisioning_app.retrieve_card(test_hash)
    assert card == test_card
    mock_repository.get.assert_called_once_with(test_hash)


@pytest.mark.asyncio
async def test_delete_card(provisioning_app, mock_repository):
    """Test deleting a card."""
    await provisioning_app.decommission_card("test_hash")
    mock_repository.delete.assert_called_once_with("test_hash")


@pytest.mark.asyncio
async def test_get_all_cards(provisioning_app, mock_repository):
    """Test retrieving all cards."""
    test_cards = [
        MCard(content=f"test{i}")
        for i in range(3)
    ]
    mock_repository.get_all.return_value = test_cards
    
    cards = await provisioning_app.list_provisioned_cards()
    assert cards == test_cards
    mock_repository.get_all.assert_called_once()


@pytest.mark.asyncio
async def test_create_card_duplicate_content_creates_event(provisioning_app, mock_repository, mock_hashing):
    """Test creating a card with duplicate content creates a reference card with deterministic hash."""
    # First card creation
    content = "test content"
    content_hash = "test_hash_1"
    mock_hashing.hash_content.return_value = content_hash
    
    # Initially no card exists
    mock_repository.get.return_value = None
    first_card = await provisioning_app.create_card(content)
    
    # Setup repository to return the first card when queried with content_hash
    mock_repository.get.side_effect = lambda h: first_card if h == content_hash else None
    
    # Second card creation with same content
    # The reference JSON content should produce a different hash
    reference_content = {
        "hash": content_hash,
        "g_time": first_card.g_time
    }
    reference_json = json.dumps(reference_content, sort_keys=True)  # Ensure consistent JSON string
    reference_hash = "reference_hash_1"  # Hash of the reference JSON
    
    # Mock hashing service to return reference_hash for the reference JSON content
    def mock_hash(c):
        if isinstance(c, bytes):
            c_str = c.decode('utf-8')
            if c_str == reference_json:
                return reference_hash
        return content_hash
    
    mock_hashing.hash_content.side_effect = mock_hash
    
    # Create card with same content - this should create a reference card
    second_card = await provisioning_app.create_card(content)
    
    # Verify both cards were saved
    assert mock_repository.save.call_count == 2  # Original card + reference card
    calls = mock_repository.save.call_args_list
    
    # First call was the original card
    assert calls[0][0][0].content == content.encode('utf-8')
    assert calls[0][0][0].hash == content_hash
    
    # Second call should be the reference card
    reference_card = calls[1][0][0]
    assert reference_card.hash == reference_hash
    assert reference_card.content == reference_json.encode('utf-8')
    
    # Verify both cards are persisted and retrievable
    # Original card should be retrievable by content_hash
    mock_repository.get.side_effect = lambda h: {
        content_hash: first_card,
        reference_hash: reference_card
    }.get(h)
    
    persisted_first_card = await mock_repository.get(content_hash)
    assert persisted_first_card is not None
    assert persisted_first_card.content == content.encode('utf-8')
    assert persisted_first_card.hash == content_hash
    
    # Reference card should be retrievable by reference_hash
    persisted_reference = await mock_repository.get(reference_hash)
    assert persisted_reference is not None
    assert persisted_reference.hash == reference_hash
    assert persisted_reference.content == reference_json.encode('utf-8')
    
    # Verify we can parse the reference and find the original content
    reference_data = json.loads(persisted_reference.content)
    assert reference_data['hash'] == content_hash
    assert reference_data['g_time'] == first_card.g_time
    
    # Using the hash from reference, we should be able to get the original content
    original_card = await mock_repository.get(reference_data['hash'])
    assert original_card is not None
    assert original_card.content == content.encode('utf-8')
    
    # Verify the reference card was created after the original
    assert datetime.fromisoformat(persisted_reference.g_time) > datetime.fromisoformat(first_card.g_time)


@pytest.mark.asyncio
async def test_create_card_collision_creates_event(provisioning_app, mock_repository, mock_hashing):
    """Test creating a card with different content but same hash creates a collision event."""
    # First card creation
    content1 = "test content 1"
    mock_hashing.hash_content.return_value = "test_hash_1"
    first_card = await provisioning_app.create_card(content1)
    
    # Setup repository to return the first card when queried
    mock_repository.get.return_value = first_card
    
    # Second card creation with different content but same hash
    content2 = "test content 2"
    mock_hashing.hash_content.return_value = "test_hash_1"  # Same hash for different content
    next_level_service = AsyncMock()
    next_level_service.hash_content.return_value = "stronger_hash"
    next_level_service.settings.algorithm = "sha256"
    mock_hashing.next_level_hash.return_value = next_level_service
    
    # Create card with different content
    await provisioning_app.create_card(content2)
    
    # Verify the event card was created with correct content
    assert mock_repository.save.call_count == 3  # Original card + event card + new card
    calls = mock_repository.save.call_args_list
    
    # First call was the original card
    assert calls[0][0][0].content == content1.encode('utf-8')
    
    # Second call was the event card
    event_card_content = json.loads(calls[1][0][0])
    assert event_card_content['event_type'] == 'collision'
    assert event_card_content['original_hash'] == first_card.hash
    assert event_card_content['original_time'] == first_card.g_time
    assert event_card_content['next_level_hash'] == "stronger_hash"
    assert event_card_content['algorithm'] == "sha256"
    
    # Third call was the new card with stronger hash
    assert calls[2][0][0].content == content2.encode('utf-8')
    assert calls[2][0][0].hash == "stronger_hash"


@pytest.mark.asyncio
async def test_create_card_no_collision(provisioning_app, mock_repository, mock_hashing):
    """Test creating a card with unique content."""
    content = "unique content"
    mock_hashing.hash_content.return_value = "unique_hash"
    
    # Setup repository to return no existing card
    mock_repository.get.return_value = None
    
    card = await provisioning_app.create_card(content)
    
    # Should create a new card without any event
    assert card.content == content.encode('utf-8')
    assert card.hash == "unique_hash"
    # Verify save was called only once
    mock_repository.save.assert_called_once()
    # Verify next_level_hash was not called
    mock_hashing.next_level_hash.assert_not_called()


@pytest.mark.asyncio
async def test_create_card_with_json_serialization_error(provisioning_app, mock_repository, mock_hashing):
    """Test creating a card when there's a JSON serialization error in the event content."""
    # First card creation
    content = "test content"
    mock_hashing.hash_content.return_value = "test_hash"
    first_card = await provisioning_app.create_card(content)
    
    # Setup repository to return the first card
    mock_repository.get.return_value = first_card
    
    # Create a non-serializable object in the next level service
    class NonSerializable:
        pass
    next_level_service = AsyncMock()
    next_level_service.hash_content.return_value = "stronger_hash"
    next_level_service.settings = NonSerializable()  # This will cause JSON serialization to fail
    mock_hashing.next_level_hash.return_value = next_level_service
    
    # Try to create duplicate card
    with pytest.raises(TypeError):  # JSON serialization will fail
        await provisioning_app.create_card(content)


@pytest.mark.asyncio
async def test_detect_duplicates_using_reference_cards(provisioning_app, mock_repository, mock_hashing):
    """Test that we can detect duplicates by checking for reference cards."""
    # Setup initial content and hashes
    content = "test content"
    content_hash = "original_hash"
    
    # Mock the hashing service to return deterministic hashes
    def mock_hash_content(c):
        if isinstance(c, bytes):
            c_str = c.decode('utf-8')
            try:
                # If content is JSON, it's a reference card
                ref_data = json.loads(c_str)
                if "hash" in ref_data and "g_time" in ref_data:
                    # Create deterministic hash for reference cards
                    return f"ref_{ref_data['hash']}"
            except json.JSONDecodeError:
                pass
            # For regular content
            if c_str == content:
                return content_hash
        return "unknown_hash"
    
    mock_hashing.hash_content.side_effect = mock_hash_content
    
    # Initially no cards exist
    stored_cards = {}
    mock_repository.get.side_effect = lambda h: stored_cards.get(h)
    mock_repository.save.side_effect = lambda card: stored_cards.update({card.hash: card})
    
    # Create first card
    first_card = await provisioning_app.create_card(content)
    assert first_card.hash == content_hash
    assert first_card.content == content.encode('utf-8')
    
    # Create duplicate card
    second_card = await provisioning_app.create_card(content)
    assert second_card.hash == f"ref_{content_hash}"  # Reference hash is deterministic
    
    # Verify reference card structure
    reference_data = json.loads(second_card.content)
    assert reference_data == {
        "hash": content_hash,
        "g_time": first_card.g_time
    }
    
    # Function to check if a card is a duplicate by looking for reference cards
    async def is_duplicate(card_hash: str) -> bool:
        # Check if there's a reference card pointing to this hash
        reference_hash = f"ref_{card_hash}"
        reference_card = await mock_repository.get(reference_hash)
        return reference_card is not None
    
    # Verify we can detect the duplicate
    assert await is_duplicate(content_hash)
    
    # Create a new unique card
    unique_content = "unique content"
    mock_hashing.hash_content.side_effect = lambda c: "unique_hash" if c == unique_content.encode('utf-8') else mock_hash_content(c)
    unique_card = await provisioning_app.create_card(unique_content)
    
    # Verify it's not detected as a duplicate
    assert not await is_duplicate("unique_hash")
    
    # Create another duplicate of the first content
    third_card = await provisioning_app.create_card(content)
    assert third_card.hash == f"ref_{content_hash}"  # Same reference hash as second card
    
    # Verify we can find all duplicates by listing reference cards
    reference_cards = [card for card in stored_cards.values() 
                      if card.hash.startswith("ref_")]
    
    # Should have 2 reference cards (second and third cards)
    assert len(reference_cards) == 2
    
    # All reference cards should point to the same original content
    for ref_card in reference_cards:
        ref_data = json.loads(ref_card.content)
        assert ref_data["hash"] == content_hash
        # Get the original content
        original = await mock_repository.get(ref_data["hash"])
        assert original.content == content.encode('utf-8')


@pytest.mark.asyncio
async def test_has_hash_for_content(provisioning_app, mock_repository, mock_hashing):
    """Test detecting duplicates for content."""
    # Setup initial content and hashes
    content = "test content"
    content_hash = "original_hash"
    
    # Mock the hashing service to return deterministic hashes
    mock_hashing.hash_content.return_value = content_hash
    
    # Initially no cards exist
    stored_cards = {}
    mock_repository.get.side_effect = lambda h: stored_cards.get(h)
    mock_repository.save.side_effect = lambda card: stored_cards.update({card.hash: card})
    
    # Initially should have no duplicates
    assert not await provisioning_app.has_hash_for_content(content)
    
    # Create first card
    first_card = await provisioning_app.create_card(content)
    
    # Now the content should be detected as existing
    assert await provisioning_app.has_hash_for_content(content)
    
    # Different content should not be detected as duplicate
    unique_content = "unique content"
    mock_hashing.hash_content.side_effect = lambda c: "unique_hash" if c == unique_content.encode('utf-8') else content_hash
    assert not await provisioning_app.has_hash_for_content(unique_content)
    
    # Create the unique content card
    unique_card = await provisioning_app.create_card(unique_content)
    
    # Now the unique content should be detected
    assert await provisioning_app.has_hash_for_content(unique_content)
    
    # Test with bytes content
    bytes_content = content.encode('utf-8')
    assert await provisioning_app.has_hash_for_content(bytes_content)
    
    # Edge cases
    assert not await provisioning_app.has_hash_for_content("")
    assert not await provisioning_app.has_hash_for_content(None)
