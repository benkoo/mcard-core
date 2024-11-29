"""Tests for basic operations in SQLite card repository."""
import pytest
import tempfile
import os
from datetime import datetime, timezone
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError, ValidationError
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def async_repository(db_path):
    """Create a SQLite repository using a temporary database."""
    repo = SQLiteStore(SQLiteConfig(db_path=db_path))
    yield repo

@pytest.fixture(autouse=True)
def cleanup_db(async_repository):
    """Clean up the database before each test."""
    conn = async_repository._get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards")
    conn.commit()
    cursor.close()
    yield

@pytest.mark.asyncio
async def test_save_and_get(async_repository):
    """Test saving and retrieving a card."""
    # Create a test card
    content = "Test content"
    g_time = datetime.now(timezone.utc).isoformat()
    card = MCard(content=content, g_time=g_time)

    # Save the card
    await async_repository.save(card)

    # Retrieve the card
    retrieved = await async_repository.get(card.hash)
    assert retrieved is not None
    assert retrieved.content == content
    assert retrieved.hash == card.hash

@pytest.mark.asyncio
async def test_get_nonexistent(async_repository):
    """Test getting a nonexistent card returns None."""
    retrieved = await async_repository.get("nonexistent_hash")
    assert retrieved is None

@pytest.mark.asyncio
async def test_save_many(async_repository):
    """Test saving multiple cards at once."""
    # Create test cards
    g_time = datetime.now(timezone.utc).isoformat()
    cards = [
        MCard(content=f"Test content {i}", g_time=g_time)
        for i in range(3)
    ]

    # Save all cards
    await async_repository.save_many(cards)

    # Verify all cards were saved
    for card in cards:
        retrieved = await async_repository.get(card.hash)
        assert retrieved is not None
        assert retrieved.content == card.content

@pytest.mark.asyncio
async def test_get_all(async_repository):
    """Test retrieving all cards with filtering and pagination."""
    # Create test cards
    g_time = datetime.now(timezone.utc).isoformat()
    cards = [
        MCard(content=f"Test content {i}", g_time=g_time)
        for i in range(5)
    ]
    await async_repository.save_many(cards)

    # Test getting all cards
    all_cards = await async_repository.get_all()
    assert len(all_cards) == 5

    # Test filtering
    filtered = await async_repository.get_all(content="content 1")
    assert len(filtered) == 1
    assert filtered[0].content == "Test content 1"

    # Test pagination
    paginated = await async_repository.get_all(limit=2, offset=1)
    assert len(paginated) == 2

@pytest.mark.asyncio
async def test_delete(async_repository):
    """Test deleting a card."""
    # Create and save a test card
    g_time = datetime.now(timezone.utc).isoformat()
    card = MCard(content="Test content", g_time=g_time)
    await async_repository.save(card)

    # Delete the card
    await async_repository.delete(card.hash)

    # Verify the card was deleted
    retrieved = await async_repository.get(card.hash)
    assert retrieved is None

@pytest.mark.asyncio
async def test_delete_all(async_repository):
    """Test deleting all cards."""
    # Create and save test cards
    g_time = datetime.now(timezone.utc).isoformat()
    cards = [
        MCard(content=f"Test content {i}", g_time=g_time)
        for i in range(3)
    ]
    await async_repository.save_many(cards)

    # Delete all cards
    await async_repository.delete_all()

    # Verify all cards were deleted
    all_cards = await async_repository.get_all()
    assert len(all_cards) == 0
