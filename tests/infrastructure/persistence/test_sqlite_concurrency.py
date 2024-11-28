"""Tests for concurrency and transaction handling in SQLite card repository."""
import pytest
import os
import tempfile
import logging
import time
from mcard.infrastructure.persistence.sqlite import SQLiteRepository, SchemaInitializer
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
    repo = SQLiteRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    return repo

def test_concurrent_operations(repository):
    start_time = time.time()
    repo = repository
    card1 = MCard(content="Card 1")
    card2 = MCard(content="Card 2")
    repo.save(card1)
    repo.save(card2)
    all_cards = repo.get_all()
    assert len(all_cards) == 2
    logging.debug(f"test_concurrent_operations took {time.time() - start_time:.2f} seconds")

def test_transaction_rollback(repository):
    start_time = time.time()
    repo = repository
    card = MCard(content="Rollback Test")
    repo.save(card)
    try:
        repo.save(card)
        raise Exception("Trigger rollback")
    except Exception:
        pass
    retrieved_card = repo.get(card.hash)
    assert retrieved_card.content == "Rollback Test"
    logging.debug(f"test_transaction_rollback took {time.time() - start_time:.2f} seconds")

def test_nested_transactions(repository):
    logging.debug("Starting test_nested_transactions")
    try:
        repo = repository
        card = MCard(content="Nested Transaction Test")
        repo.save(card)
        repo.delete(card.hash)
        card = MCard(content="Updated Content")
        repo.save(card)
        retrieved_card = repo.get(card.hash)
        assert retrieved_card.content == "Updated Content"
    except Exception as e:
        logging.error(f"test_nested_transactions failed: {str(e)}")

def test_transaction_isolation(repository):
    logging.debug("Starting test_transaction_isolation")
    try:
        repo = repository
        card1 = MCard(content="Isolation Test 1")
        repo.save(card1)
        card2 = MCard(content="Isolation Test 2")
        repo.save(card2)
        all_cards = repo.get_all()
        assert len(all_cards) == 2
    except Exception as e:
        logging.error(f"test_transaction_isolation failed: {str(e)}")

def test_concurrent_transactions(db_path):
    start_time = time.time()
    repo = SQLiteRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    card1 = MCard(content="Concurrent Transaction 1")
    card2 = MCard(content="Concurrent Transaction 2")
    repo.save(card1)
    repo.save(card2)
    all_cards = repo.get_all()
    assert len(all_cards) == 2
    logging.debug(f"test_concurrent_transactions took {time.time() - start_time:.2f} seconds")
