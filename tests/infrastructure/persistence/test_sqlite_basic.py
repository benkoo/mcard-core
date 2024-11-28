"""Tests for basic operations in SQLite card repository."""
import pytest
from datetime import datetime, timezone
from mcard.infrastructure.persistence.sqlite import SQLiteRepository, SchemaInitializer
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
def repository(db_path):
    """Fixture for SQLite repository using synchronous sqlite3."""
    repo = SQLiteRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    return repo

def test_save_and_get_card(repository):
    """Test saving and retrieving a card."""
    repo = repository
    content = "Test content"
    card = MCard(content=content)
    repo.save(card)
    retrieved_card = repo.get(card.hash)
    assert retrieved_card.content == content

def test_get_nonexistent_card(repository):
    """Test retrieving a non-existent card."""
    repo = repository
    with pytest.raises(StorageError, match="Failed to retrieve card: Card with hash nonexistent_hash not found."):
        repo.get("nonexistent_hash")

def test_save_large_content(repository):
    """Test saving content larger than max size."""
    repo = repository
    content = "x" * (repo.max_content_size + 1)
    card = MCard(content=content)
    with pytest.raises(ValidationError, match=f"Content size exceeds maximum limit of {repo.max_content_size} bytes"):
        repo.save(card)

def test_get_all_cards(repository):
    """Test retrieving all cards."""
    repo = repository
    card1 = MCard(content="Content 1")
    card2 = MCard(content="Content 2")
    repo.save(card1)
    repo.save(card2)
    cards = repo.get_all()
    assert len(cards) == 2
    assert cards[0].content == "Content 2"
    assert cards[1].content == "Content 1"

def test_delete_card(repository):
    """Test deleting a card."""
    repo = repository
    card = MCard(content="To be deleted")
    repo.save(card)
    repo.delete(card.hash)
    with pytest.raises(StorageError, match=f"Failed to retrieve card: Card with hash {card.hash} not found."):
        repo.get(card.hash)

def test_delete_nonexistent_card(repository):
    """Test deleting a non-existent card."""
    repo = repository
    with pytest.raises(StorageError, match="Failed to delete card: Card with hash nonexistent_hash not found."):
        repo.delete("nonexistent_hash")
