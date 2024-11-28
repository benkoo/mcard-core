"""Tests for concurrency in SQLite card repository."""
import pytest
import asyncio
import logging
from datetime import datetime, timezone
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.infrastructure.persistence.schema_initializer import SchemaInitializer
from mcard.domain.models.card import MCard
import tempfile
import os
import time
from mcard.domain.models.exceptions import StorageError

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
def db_path():
    """Fixture for temporary database path."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup after tests
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def repository(db_path):
    """Fixture for SQLite repository."""
    repo = SQLiteRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    return repo

@pytest.mark.asyncio
async def test_concurrent_operations(repository):
    """Test concurrent operations on the repository."""
    repo = repository
    start_time = time.time()

    # Create multiple cards concurrently
    cards = [MCard(content=f"Content {i}") for i in range(10)]
    tasks = [repo.save(card) for card in cards]
    await asyncio.gather(*tasks)

    # Verify all cards were saved
    saved_cards = await repo.get_all()
    assert len(saved_cards) == len(cards)

    # Test concurrent reads
    tasks = [repo.get(card.hash) for card in cards]
    retrieved_cards = await asyncio.gather(*tasks)
    assert len(retrieved_cards) == len(cards)

    logging.debug(f"test_concurrent_operations took {time.time() - start_time:.2f} seconds")

@pytest.mark.asyncio
async def test_transaction_rollback(repository):
    """Test transaction rollback on error."""
    repo = repository
    start_time = time.time()

    # Create a card
    card = MCard(content="Test content")
    await repo.save(card)

    # Try to save an invalid card
    invalid_card = MCard(content="x" * (repo.max_content_size + 1))
    with pytest.raises(Exception):
        await repo.save(invalid_card)

    # Verify the first card is still there
    saved_card = await repo.get(card.hash)
    assert saved_card.content == "Test content"

    logging.debug(f"test_transaction_rollback took {time.time() - start_time:.2f} seconds")

@pytest.mark.asyncio
async def test_nested_transactions(repository):
    """Test nested transactions."""
    repo = repository
    card = MCard(content="Test content")
    await repo.save(card)
    await repo.delete(card.hash)
    with pytest.raises(StorageError):
        await repo.get(card.hash)

@pytest.mark.asyncio
async def test_transaction_isolation(repository):
    """Test transaction isolation."""
    repo = repository
    card1 = MCard(content="Isolation Test 1")
    card2 = MCard(content="Isolation Test 2")
    await repo.save(card1)
    await repo.save(card2)
    all_cards = await repo.get_all()
    assert len(all_cards) == 2

@pytest.mark.asyncio
async def test_concurrent_transactions(db_path):
    """Test concurrent transactions."""
    start_time = time.time()
    repo1 = SQLiteRepository(db_path)
    repo2 = SQLiteRepository(db_path)

    # Create cards in both repositories
    card1 = MCard(content="Content from repo1")
    card2 = MCard(content="Content from repo2")

    await asyncio.gather(
        repo1.save(card1),
        repo2.save(card2)
    )

    # Verify both cards are accessible from both repositories
    saved_cards1 = await repo1.get_all()
    saved_cards2 = await repo2.get_all()

    assert len(saved_cards1) == 2
    assert len(saved_cards2) == 2

    logging.debug(f"test_concurrent_transactions took {time.time() - start_time:.2f} seconds")
