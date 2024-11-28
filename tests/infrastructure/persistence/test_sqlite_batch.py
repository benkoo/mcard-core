"""Tests for batch operations in SQLite card repository."""
import pytest
import asyncio
from datetime import datetime, timezone
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.infrastructure.persistence.schema_initializer import SchemaInitializer
from mcard.domain.models.card import MCard
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
    repo = SQLiteRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    yield repo
    os.close(db_fd)
    os.unlink(db_path)

@pytest.mark.asyncio
async def test_save_many_and_get_many(repository):
    """Test saving and retrieving multiple cards."""
    repo = repository
    cards = [MCard(content=f"Content {i}") for i in range(5)]
    await repo.save_many(cards)
    retrieved_cards = await repo.get_many([card.hash for card in cards])
    assert len(retrieved_cards) == len(cards)
    # Adjusting the order to match the descending g_time order
    for original, retrieved in zip(reversed(cards), retrieved_cards):
        # Decode content for comparison if needed
        if isinstance(retrieved.content, bytes):
            retrieved_content = retrieved.content.decode('utf-8')
        else:
            retrieved_content = retrieved.content
        assert original.content == retrieved_content

@pytest.mark.asyncio
async def test_get_all_with_pagination(repository):
    """Test retrieving all cards with pagination."""
    repo = repository
    cards = [MCard(content=f"Content {i}") for i in range(10)]
    await repo.save_many(cards)
    all_cards = await repo.get_all(limit=5)
    assert len(all_cards) == 5
    assert all_cards[0].content == "Content 9"
    assert all_cards[4].content == "Content 5"

@pytest.mark.asyncio
async def test_mixed_content_batch(repository):
    """Test saving and retrieving mixed content types in batch."""
    repo = repository
    cards = [
        MCard(content=b"Binary content", g_time="2023-10-01T10:00:00Z"),
        MCard(content="Text content", g_time="2023-10-01T09:00:00Z")
    ]
    await repo.save_many(cards)
    retrieved_cards = await repo.get_many([card.hash for card in cards])
    assert len(retrieved_cards) == len(cards)
    # Ensure the order is correct based on g_time
    # Decode content for comparison if needed
    if isinstance(retrieved_cards[0].content, bytes):
        retrieved_binary_content = retrieved_cards[0].content.decode('utf-8')
    else:
        retrieved_binary_content = retrieved_cards[0].content
    assert retrieved_binary_content == "Binary content"

    if isinstance(retrieved_cards[1].content, bytes):
        retrieved_text_content = retrieved_cards[1].content.decode('utf-8')
    else:
        retrieved_text_content = retrieved_cards[1].content
    assert retrieved_text_content == "Text content"
