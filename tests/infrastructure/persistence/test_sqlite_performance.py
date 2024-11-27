"""Performance tests for SQLite card repository."""
import pytest
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository
from mcard.domain.models.card import MCard
import time
import os
import tempfile
import asyncio

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
    repo = SQLiteCardRepository(db_path)
    asyncio.run(repo._init_db())
    yield repo
    # Ensure database connection is closed after tests
    asyncio.run(repo.close_connection())

@pytest.mark.asyncio
async def test_write_performance(repository):
    repo = repository
    start_time = time.time()
    cards = [MCard(content=f"Card {i}") for i in range(100)]
    await repo.save_many(cards)
    duration = time.time() - start_time
    assert duration < 5  # Ensure it completes within 5 seconds

@pytest.mark.asyncio
async def test_read_performance(repository):
    repo = repository
    cards = [MCard(content=f"Card {i}") for i in range(100)]
    await repo.save_many(cards)
    start_time = time.time()
    retrieved_cards = await repo.get_all()
    duration = time.time() - start_time
    assert len(retrieved_cards) == 100
    assert duration < 5  # Ensure it completes within 5 seconds
