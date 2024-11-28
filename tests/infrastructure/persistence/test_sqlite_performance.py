"""Tests for performance in SQLite card repository."""
import pytest
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.infrastructure.persistence.schema_initializer import SchemaInitializer
from mcard.domain.models.card import MCard
import time
import os
import tempfile
import asyncio
import logging

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
    yield repo
    # Ensure database connection is closed after tests
    repo.connection.close()

@pytest.mark.asyncio
async def test_write_performance(repository):
    repo = repository
    start_time = time.time()
    cards = [MCard(content=f"Card {i}") for i in range(100)]
    await repo.save_many(cards)  # Call save_many asynchronously
    end_time = time.time()
    logging.debug(f"Write performance test completed in {end_time - start_time} seconds.")

@pytest.mark.asyncio
async def test_read_performance(repository):
    repo = repository
    cards = [MCard(content=f"Card {i}") for i in range(100)]
    await repo.save_many(cards)  # Call save_many asynchronously
    start_time = time.time()
    retrieved_cards = await repo.get_all()
    end_time = time.time()
    logging.debug(f"Read performance test completed in {end_time - start_time} seconds.")
