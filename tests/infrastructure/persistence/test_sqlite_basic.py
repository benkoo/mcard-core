"""Tests for basic operations in SQLite card repository."""
import pytest
from datetime import datetime, timezone
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.infrastructure.persistence.schema_initializer import SchemaInitializer
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError, ValidationError
import tempfile
import os

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
async def test_save_and_get_card(repository):
    """Test saving and retrieving a card."""
    repo = repository
    content = "Test content"
    card = MCard(content=content)
    await repo.save(card)
    retrieved_card = await repo.get(card.hash)
    assert retrieved_card.content == content

@pytest.mark.asyncio
async def test_get_nonexistent_card(repository):
    """Test retrieving a non-existent card."""
    repo = repository
    with pytest.raises(StorageError, match="Failed to retrieve card: Card with hash nonexistent_hash not found."):
        await repo.get("nonexistent_hash")

@pytest.mark.asyncio
async def test_save_large_content(repository):
    """Test saving content larger than max size."""
    repo = repository
    content = "x" * (repo.max_content_size + 1)
    card = MCard(content=content)
    with pytest.raises(ValidationError, match=f"Content size exceeds maximum limit of {repo.max_content_size} bytes"):
        await repo.save(card)

@pytest.mark.asyncio
async def test_get_all_cards(repository):
    """Test retrieving all cards."""
    repo = repository
    card1 = MCard(content="Content 1")
    card2 = MCard(content="Content 2")
    await repo.save(card1)
    await repo.save(card2)
    cards = await repo.get_all()
    assert len(cards) == 2
    assert cards[0].content == "Content 2"
    assert cards[1].content == "Content 1"

@pytest.mark.asyncio
async def test_delete_card(repository):
    """Test deleting a card."""
    repo = repository
    card = MCard(content="To be deleted")
    await repo.save(card)
    await repo.delete(card.hash)
    with pytest.raises(StorageError, match=f"Failed to retrieve card: Card with hash {card.hash} not found."):
        await repo.get(card.hash)

@pytest.mark.asyncio
async def test_delete_nonexistent_card(repository):
    """Test deleting a non-existent card."""
    repo = repository
    with pytest.raises(StorageError, match="Failed to delete card: Card with hash nonexistent_hash not found."):
        await repo.delete("nonexistent_hash")
