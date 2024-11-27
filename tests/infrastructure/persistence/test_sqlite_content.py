"""Tests for content handling in SQLite card repository."""
import pytest
import os
import tempfile
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository
from mcard.domain.models.card import MCard
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
    return SQLiteCardRepository(db_path)

@pytest.mark.asyncio
async def test_binary_content(repository):
    repo = repository
    async with repo as repo:
        binary_content = bytes([0, 1, 2, 3, 4])
        card = MCard(content=binary_content)
        await repo.save(card)
        retrieved_card = await repo.get(card.hash)
        assert retrieved_card.content == binary_content

@pytest.mark.asyncio
async def test_large_content_handling(db_path):
    repo = SQLiteCardRepository(db_path)
    logging.debug("Testing large content handling")
    async with repo as repo:
        large_content = "x" * (repo.max_content_size - 1)
        card = MCard(content=large_content)
        await repo.save(card)
        retrieved_card = await repo.get(card.hash)
        assert retrieved_card.content == large_content

@pytest.mark.asyncio
async def test_binary_and_text_content(db_path):
    repo = SQLiteCardRepository(db_path)
    logging.debug("Testing binary and text content handling")
    async with repo as repo:
        text_content = MCard(content="Text Content")
        binary_content = MCard(content=bytes([0, 1, 2, 3, 4]))
        await repo.save_many([text_content, binary_content])
        retrieved_text = await repo.get(text_content.hash)
        retrieved_binary = await repo.get(binary_content.hash)
        assert retrieved_text.content == "Text Content"
        assert retrieved_binary.content == bytes([0, 1, 2, 3, 4])
