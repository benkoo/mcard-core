"""Tests for batch operations and pagination in SQLite card repository."""
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
async def repository(db_path):
    """Fixture for SQLite repository."""
    repo = SQLiteCardRepository(db_path)
    await repo._init_db()
    return repo

@pytest.mark.asyncio
async def test_save_many_and_get_many(repository):
    repo = await repository
    async with repo as repo:
        cards = [MCard(content=f"Card {i}") for i in range(5)]
        await repo.save_many(cards)
        retrieved_cards = await repo.get_many([card.hash for card in cards])
        for i, card in enumerate(retrieved_cards):
            logging.debug(f"Card {i}: Hash={card.hash}, Content={card.content}")
        assert len(retrieved_cards) == 5

@pytest.mark.asyncio
async def test_get_all_with_pagination(repository):
    repo = await repository
    async with repo as repo:
        cards = [MCard(content=f"Card {i}") for i in range(10)]
        await repo.save_many(cards)
        page1 = await repo.get_all(limit=5, offset=0)
        page2 = await repo.get_all(limit=5, offset=5)
        assert len(page1) == 5
        assert len(page2) == 5

@pytest.mark.asyncio
async def test_mixed_content_batch(repository):
    repo = await repository
    async with repo as repo:
        text_content = MCard(content="Text Content")
        binary_content = MCard(content=bytes([0, 1, 2, 3, 4]))
        await repo.save_many([text_content, binary_content])
        retrieved_cards = await repo.get_many([text_content.hash, binary_content.hash])
        # Sort retrieved cards by hash to ensure consistent order
        retrieved_cards.sort(key=lambda card: card.hash)
        expected_cards = sorted([text_content, binary_content], key=lambda card: card.hash)
        for i, card in enumerate(retrieved_cards):
            logging.debug(f"Card {i}: Hash={card.hash}, Content={card.content}")
        logging.debug(f"Retrieved cards: {retrieved_cards}")
        # Compare against expected sorted order
        assert retrieved_cards[0].content == expected_cards[0].content
        assert retrieved_cards[1].content == expected_cards[1].content
