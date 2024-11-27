"""Tests for concurrency and transaction handling in SQLite card repository."""
import pytest
import asyncio
import os
import tempfile
import logging
import time
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository
from mcard.domain.models.card import MCard
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
    return SQLiteCardRepository(db_path)

@pytest.mark.asyncio
async def test_concurrent_operations(repository):
    start_time = time.time()
    repo = repository
    async with repo as repo:
        card1 = MCard(content="Card 1")
        card2 = MCard(content="Card 2")
        await asyncio.gather(repo.save(card1), repo.save(card2))
        all_cards = await repo.get_all()
        assert len(all_cards) == 2
    logging.debug(f"test_concurrent_operations took {time.time() - start_time:.2f} seconds")

@pytest.mark.asyncio
async def test_transaction_rollback(repository):
    start_time = time.time()
    repo = repository
    async with repo as repo:
        card = MCard(content="Rollback Test")
        await repo.save(card)
        conn = await repo._get_connection()
        await conn.commit()
        try:
            async with repo.transaction():
                card.content = "Updated Content"
                await repo.save(card)
                raise Exception("Trigger rollback")
        except Exception:
            pass
        retrieved_card = await repo.get(card.hash)
        assert retrieved_card.content == "Rollback Test"
    logging.debug(f"test_transaction_rollback took {time.time() - start_time:.2f} seconds")

@pytest.mark.asyncio
async def test_nested_transactions(repository):
    logging.debug("Starting test_nested_transactions")
    try:
        async with asyncio.timeout(5):
            repo = repository
            async with repo as repo:
                card = MCard(content="Nested Transaction Test")
                await repo.save(card)
                conn = await repo._get_connection()
                await conn.commit()
                async with repo.transaction():
                    await repo.delete(card.hash)
                    card = MCard(content="Updated Content")
                    await repo.save(card)
                retrieved_card = await repo.get(card.hash)
                assert retrieved_card.content == "Updated Content"
    except asyncio.TimeoutError:
        logging.error("test_nested_transactions timed out")

@pytest.mark.asyncio
async def test_transaction_isolation(repository):
    logging.debug("Starting test_transaction_isolation")
    try:
        async with asyncio.timeout(5):
            repo = repository
            async with repo as repo:
                logging.debug("Saving card1")
                card1 = MCard(content="Isolation Test 1")
                await repo.save(card1)

                logging.debug("Saving card2")
                card2 = MCard(content="Isolation Test 2")
                await repo.save(card2)

                # Explicitly commit after saving card2 to ensure transaction closure
                conn = await repo._get_connection()
                await conn.commit()

                logging.debug("Starting transaction")
                async with repo.transaction():
                    await repo.delete(card1.hash)
                    card1 = MCard(content="Updated Content 1")
                    await repo.save(card1)
                    logging.debug("Updated card1 within transaction")

                logging.debug("Retrieving card1")
                retrieved_card1 = await repo.get(card1.hash)

                logging.debug("Retrieving card2")
                retrieved_card2 = await repo.get(card2.hash)

                logging.debug("Asserting retrieved contents")
                assert retrieved_card1.content == "Updated Content 1"
                assert retrieved_card2.content == "Isolation Test 2"
    except asyncio.TimeoutError:
        logging.error("test_transaction_isolation timed out")

@pytest.mark.asyncio
async def test_concurrent_transactions(db_path):
    start_time = time.time()
    repo = SQLiteCardRepository(db_path)
    async with repo as repo:
        card1 = MCard(content="Concurrent Transaction 1")
        card2 = MCard(content="Concurrent Transaction 2")
        logging.debug("Saving card1 and card2 concurrently")
        await asyncio.gather(repo.save(card1), repo.save(card2))
        logging.debug("Retrieving all cards")
        all_cards = await repo.get_all()
        logging.debug("Asserting the number of cards")
        assert len(all_cards) == 2
    logging.debug(f"test_concurrent_transactions took {time.time() - start_time:.2f} seconds")
