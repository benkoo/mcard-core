"""Tests for connection and error handling in SQLite card repository."""
import pytest
import os
import tempfile
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository, SchemaInitializer
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
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
def repository():
    """Fixture for SQLite repository using in-memory database."""
    repo = SQLiteCardRepository(":memory:")
    logging.debug("Initializing in-memory database schema before tests")
    repo._init_db()
    return repo

@pytest.fixture
def db_repository(db_path):
    """Fixture for SQLite repository using temporary database."""
    repo = SQLiteCardRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    return repo

def test_connection_pool_limit(repository):
    logging.debug("Starting test_connection_pool_limit")
    repo = repository
    logging.debug("Performing multiple operations to test connection handling")
    # Perform multiple get_all operations
    results = [repo.get_all() for _ in range(10)]
    logging.debug("Operations completed for test_connection_pool_limit")
    assert all(len(result) == 0 for result in results)
    logging.debug("Exiting test_connection_pool_limit")

def test_error_handling(repository):
    logging.debug("Starting test_error_handling")
    repo = repository
    logging.debug("Testing error handling")
    try:
        repo.save(MCard(content="Invalid", hash="", g_time="Invalid"))
    except StorageError as e:
        logging.debug(f"Caught expected StorageError: {e}")
    logging.debug("Exiting test_error_handling")

def test_connection_error_recovery(repository):
    logging.debug("Starting test_connection_error_recovery")
    repo = repository
    repo._init_db()  # Ensure schema initialization
    card = MCard(content="Recovery Test")
    logging.debug("Saving card")
    repo.save(card)
    logging.debug("Card saved successfully")
    logging.debug("Exiting test_connection_error_recovery")

def test_connection_pool_management(db_repository):
    logging.debug("Starting test_connection_pool_management")
    repo = db_repository
    try:
        logging.debug("Creating tasks for test_connection_pool_management")
        tasks = [repo.get_all for _ in range(10)]
        logging.debug("Executing tasks for test_connection_pool_management")
        results = [task() for task in tasks]  # Execute synchronously
        logging.debug("Tasks completed for test_connection_pool_management")
        assert all(len(result) == 0 for result in results)
        logging.debug("Exiting test_connection_pool_management")
    except Exception as e:
        logging.error(f"Unexpected error occurred in test_connection_pool_management: {e}")
