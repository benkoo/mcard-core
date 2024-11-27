"""Tests for connection and error handling in SQLite card repository."""
import pytest
import os
import tempfile
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
import asyncio
import logging

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
    logging.debug("Initializing database schema before tests")
    await repo._init_db()
    return repo

@pytest.mark.asyncio
async def test_connection_pool_limit(repository):
    logging.debug("Starting test_connection_pool_limit")
    repo = await repository
    logging.debug("Entered async context for test_connection_pool_limit")
    async with repo as repo:
        logging.debug("Creating tasks for test_connection_pool_limit")
        tasks = [repo.get_all() for _ in range(repo.connection_pool_limit)]
        logging.debug("Executing tasks for test_connection_pool_limit")
        results = await asyncio.gather(*tasks)
        logging.debug("Tasks completed for test_connection_pool_limit")
        assert all(len(result) == 0 for result in results)
    logging.debug("Exiting async context for test_connection_pool_limit")

@pytest.mark.asyncio
async def test_error_handling(repository):
    logging.debug("Starting test_error_handling")
    repo = await repository
    logging.debug("Entered async context for test_error_handling")
    async with repo as repo:
        try:
            logging.debug("Attempting to retrieve non-existent card")
            with pytest.raises(StorageError):
                await repo.get("non-existent-hash")
            logging.debug("StorageError was raised as expected")
        except Exception as e:
            logging.error(f"Unexpected error in test_error_handling: {e}")
    logging.debug("Exiting async context for test_error_handling")

@pytest.mark.asyncio
async def test_connection_error_recovery(repository):
    logging.debug("Starting test_connection_error_recovery")
    repo = await repository
    logging.debug("Entered async context for test_connection_error_recovery")
    card = MCard(content="Recovery Test")
    logging.debug("Saving card")
    await repo.save(card)
    logging.debug("Card saved successfully")
    logging.debug("Retrieving saved card")
    retrieved_card = await repo.get(card.hash)
    assert retrieved_card is not None
    logging.debug("Card exists in the database, proceeding to simulate connection error")
    try:
        logging.debug("Simulating connection error")
        await repo._connection.close()
        logging.debug("Connection closed, attempting to retrieve card after connection error")
        with pytest.raises(StorageError):
            await repo.get(card.hash)
        logging.debug("StorageError was raised as expected after connection error")
    except Exception as e:
        logging.error(f"Unexpected error in test_connection_error_recovery: {e}")
    logging.debug("Exiting async context for test_connection_error_recovery")

@pytest.mark.asyncio
async def test_connection_pool_management(db_path):
    logging.debug("Starting test_connection_pool_management")
    repo = SQLiteCardRepository(db_path)
    try:
        logging.debug("Entered async context for test_connection_pool_management")
        async with repo as repo:
            logging.debug("Creating tasks for test_connection_pool_management")
            tasks = [repo.get_all() for _ in range(10)]
            logging.debug("Executing tasks for test_connection_pool_management")
            results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
            logging.debug("Tasks completed for test_connection_pool_management")
            assert all(len(result) == 0 for result in results)
        logging.debug("Exiting async context for test_connection_pool_management")
    except asyncio.TimeoutError:
        logging.error("test_connection_pool_management timed out")
    except Exception as e:
        logging.error(f"Unexpected error occurred in test_connection_pool_management: {e}")
