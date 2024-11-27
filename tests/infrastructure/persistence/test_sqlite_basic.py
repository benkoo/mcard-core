"""Tests for basic operations in SQLite card repository."""
import pytest
from datetime import datetime, timezone
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError, ValidationError
import tempfile
import os

@pytest.fixture
def db_path():
    """Fixture for temporary database path."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    yield temp_path
    try:
        os.unlink(temp_path)
    except OSError:
        pass  # File might be locked or already deleted

@pytest.fixture
async def repository(db_path):
    """Fixture for SQLite repository."""
    return SQLiteCardRepository(db_path)

@pytest.mark.asyncio
async def test_save_and_get_card(repository):
    """Test saving and retrieving a card."""
    repo = await repository
    async with repo as repo:
        content = "Test content"
        card = MCard(content=content)
        await repo.save(card)
        retrieved_card = await repo.get(card._hash)
        assert retrieved_card.content == content

@pytest.mark.asyncio
async def test_get_nonexistent_card(repository):
    """Test retrieving a non-existent card."""
    repo = await repository
    async with repo as repo:
        with pytest.raises(StorageError):
            await repo.get("nonexistent-id")

@pytest.mark.asyncio
async def test_save_large_content(repository):
    """Test saving content larger than max size."""
    repo = await repository
    async with repo as repo:
        large_content = "x" * (repo.max_content_size + 1)
        card = MCard(content=large_content)
        with pytest.raises(StorageError):
            await repo.save(card)

@pytest.mark.asyncio
async def test_get_all_cards(repository):
    """Test retrieving all cards."""
    repo = await repository
    async with repo as repo:
        card1 = MCard(content="Card 1")
        card2 = MCard(content="Card 2")
        await repo.save(card1)
        await repo.save(card2)
        all_cards = await repo.get_all()
        assert len(all_cards) == 2

@pytest.mark.asyncio
async def test_delete_card(repository):
    """Test deleting a card."""
    repo = await repository
    async with repo as repo:
        card = MCard(content="To be deleted")
        await repo.save(card)
        await repo.delete(card._hash)
        with pytest.raises(StorageError):
            await repo.get(card._hash)

@pytest.mark.asyncio
async def test_delete_nonexistent_card(repository):
    """Test deleting a non-existent card."""
    repo = await repository
    async with repo as repo:
        with pytest.raises(StorageError):
            await repo.delete("non_existent_hash")
