"""Tests for batch operations in SQLite card repository."""
import pytest
from datetime import datetime, timezone
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
import tempfile
import os
import logging

# Ensure the log file is cleared before each test run
if os.path.exists('test.log'):
    os.remove('test.log')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('test.log')  # Output to file
    ]
)

@pytest.fixture
def repository():
    """Create a temporary SQLite repository for testing."""
    db_fd, db_path = tempfile.mkstemp()
    try:
        repo = SQLiteStore(SQLiteConfig(db_path=db_path))
        yield repo
    finally:
        os.close(db_fd)
        os.unlink(db_path)

def test_save_many_and_get_many(repository):
    """Test saving and retrieving multiple cards."""
    cards = [MCard(content=f"Content {i}", g_time=f"2023-01-01T{i:02d}:00:00Z") for i in range(5)]
    repository.save_many(cards)
    
    # Get cards one by one to verify individual retrieval
    for card in cards:
        retrieved = repository.get(card.hash)
        assert retrieved.content == card.content
        assert retrieved.g_time == card.g_time
    
    # Verify batch retrieval works
    retrieved_cards = repository.get_many([card.hash for card in cards])
    assert len(retrieved_cards) == len(cards)
    
    # Create lookup by hash since order may not be preserved
    retrieved_dict = {card.hash: card for card in retrieved_cards}
    for card in cards:
        assert retrieved_dict[card.hash].content == card.content
        assert retrieved_dict[card.hash].g_time == card.g_time

def test_get_all_cards(repository):
    """Test retrieving all cards."""
    cards = [MCard(content=f"Content {i}") for i in range(10)]
    repository.save_many(cards)
    all_cards = repository.get_all()
    assert len(all_cards) == 10
    
    # Verify content of cards
    card_contents = {card.content for card in all_cards}
    expected_contents = {f"Content {i}" for i in range(10)}
    assert card_contents == expected_contents

def test_mixed_content_batch(repository):
    """Test saving and retrieving mixed content types in batch."""
    binary_content = b"Binary content"
    text_content = "Text content"
    
    cards = [
        MCard(content=binary_content, g_time="2023-10-01T10:00:00Z"),
        MCard(content=text_content, g_time="2023-10-01T09:00:00Z")
    ]
    repository.save_many(cards)
    
    # Get cards individually to verify content
    binary_card = repository.get(cards[0].hash)
    text_card = repository.get(cards[1].hash)
    
    assert binary_card.content == binary_content
    assert text_card.content == text_content
    
    # Verify batch retrieval
    retrieved_cards = repository.get_many([card.hash for card in cards])
    assert len(retrieved_cards) == len(cards)
    
    # Create lookup by hash
    retrieved_dict = {card.hash: card for card in retrieved_cards}
    assert retrieved_dict[cards[0].hash].content == binary_content
    assert retrieved_dict[cards[1].hash].content == text_content

def test_empty_batch_operations(repository):
    """Test handling of empty batch operations."""
    # Test empty save_many
    repository.save_many([])
    
    # Test empty get_many
    empty_cards = repository.get_many([])
    assert len(empty_cards) == 0
    
    # Test get_all on empty repository
    all_cards = repository.get_all()
    assert len(all_cards) == 0

def test_duplicate_save_batch(repository):
    """Test saving duplicate cards in batch."""
    # Create two cards with different content
    card1 = MCard(content="Content One")
    card2 = MCard(content="Content Two")
    
    # Save both cards
    repository.save_many([card1, card2])
    
    # Try to save card1 again
    with pytest.raises(StorageError, match="Failed to save cards: UNIQUE constraint failed: cards.hash"):
        repository.save_many([card1])
    
    # Verify original cards are still there
    all_cards = repository.get_all()
    assert len(all_cards) == 2
    contents = {card.content for card in all_cards}
    assert "Content One" in contents
    assert "Content Two" in contents
