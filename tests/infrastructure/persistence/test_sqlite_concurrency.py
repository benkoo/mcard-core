"""Tests for concurrent operations in SQLite card repository."""
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType
import tempfile
import os
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
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def repository(db_path):
    """Fixture for SQLite repository."""
    repo = SQLiteStore(SQLiteConfig(db_path=db_path))
    return repo

def test_concurrent_reads(repository):
    """Test concurrent read operations."""
    # Create test data
    cards = [MCard(content=f"Content {i}") for i in range(10)]
    for card in cards:
        repository.save(card)

    def read_card(card_hash):
        thread_repo = SQLiteStore(SQLiteConfig(db_path=repository.db_path))
        retrieved_card = thread_repo.get(card_hash)
        assert retrieved_card is not None
        return retrieved_card

    # Test concurrent reads using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(read_card, card.hash) for card in cards]
        results = [future.result() for future in futures]

    assert len(results) == len(cards)
    assert all(isinstance(card, MCard) for card in results)

def test_concurrent_writes(repository):
    """Test concurrent write operations."""
    def save_card(content):
        thread_repo = SQLiteStore(SQLiteConfig(db_path=repository.db_path))
        card = MCard(content=content)
        thread_repo.save(card)
        return card.hash

    # Test concurrent writes using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(save_card, f"Concurrent content {i}") for i in range(10)]
        card_hashes = [future.result() for future in futures]

    # Verify all cards were saved
    saved_cards = repository.get_all()
    assert len(saved_cards) == 10
    assert all(card.hash in card_hashes for card in saved_cards)

def test_read_write_isolation(repository):
    """Test isolation between concurrent reads and writes."""
    initial_cards = [MCard(content=f"Initial {i}") for i in range(5)]
    for card in initial_cards:
        repository.save(card)

    read_results = []
    write_complete = threading.Event()

    def reader_thread():
        thread_repo = SQLiteStore(SQLiteConfig(db_path=repository.db_path))
        while not write_complete.is_set():
            cards = thread_repo.get_all()
            read_results.append(len(cards))
            time.sleep(0.01)

    def writer_thread():
        thread_repo = SQLiteStore(SQLiteConfig(db_path=repository.db_path))
        for i in range(5):
            card = MCard(content=f"Additional {i}")
            thread_repo.save(card)
            time.sleep(0.02)
        write_complete.set()

    # Start reader and writer threads
    reader = threading.Thread(target=reader_thread)
    writer = threading.Thread(target=writer_thread)

    reader.start()
    writer.start()

    writer.join()
    reader.join()

    # Verify final state
    final_cards = repository.get_all()
    assert len(final_cards) == 10  # 5 initial + 5 additional
    # Each read should see a consistent state (no partial transactions)
    assert all(count in [5,6,7,8,9,10] for count in read_results)

def test_concurrent_deletes(repository):
    """Test concurrent delete operations."""
    # Create test data
    cards = [MCard(content=f"Delete test {i}") for i in range(10)]
    for card in cards:
        repository.save(card)

    def delete_card(card_hash):
        thread_repo = SQLiteStore(SQLiteConfig(db_path=repository.db_path))
        try:
            thread_repo.delete(card_hash)
            return True
        except StorageError:
            return False

    # Test concurrent deletes
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(delete_card, card.hash) for card in cards]
        results = [future.result() for future in futures]

    # Verify all cards were deleted
    remaining_cards = repository.get_all()
    assert len(remaining_cards) == 0

def test_transaction_rollback(repository):
    """Test transaction rollback under concurrent operations."""
    def save_invalid_card():
        # Use a smaller max_content_size for testing
        config = SQLiteConfig(db_path=repository.db_path, max_content_size=1024)  # 1KB limit
        thread_repo = SQLiteStore(config)
        try:
            card = MCard(content="x" * 2048)  # 2KB content, exceeds limit
            thread_repo.save(card)
        except StorageError:
            return True
        return False

    def save_valid_card(content):
        # Use same config as main repository
        thread_repo = SQLiteStore(SQLiteConfig(db_path=repository.db_path))
        try:
            card = MCard(content=content)
            thread_repo.save(card)
            return card.hash
        except StorageError:
            return None

    # Run concurrent valid and invalid operations
    with ThreadPoolExecutor(max_workers=5) as executor:
        invalid_futures = [executor.submit(save_invalid_card) for _ in range(3)]
        valid_futures = [executor.submit(save_valid_card, f"Valid content {i}") for i in range(5)]

        invalid_results = [future.result() for future in invalid_futures]
        valid_hashes = [future.result() for future in valid_futures]

    # Verify operations succeeded/failed as expected
    assert all(invalid_results)  # All invalid operations should have failed
    assert any(h is not None for h in valid_hashes)  # Some valid operations should have succeeded
    
    # Verify database state
    final_cards = repository.get_all()
    assert len(final_cards) == len([h for h in valid_hashes if h is not None])  # Only valid cards should be present
