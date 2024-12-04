"""Tests for performance characteristics of SQLite card repository."""
import pytest
import tempfile
import os
import time
import concurrent.futures
from datetime import datetime, timezone
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.domain.models.card import MCard
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def repository(db_path):
    """Fixture for SQLite repository."""
    repo = SQLiteStore(SQLiteConfig(db_path=db_path))
    yield repo

def test_write_performance(repository):
    """Test write performance."""
    start_time = time.time()
    num_cards = 1000
    
    for i in range(num_cards):
        card = MCard(content=f"Content {i}")
        repository.save(card)
    
    duration = time.time() - start_time
    logging.info(f"Wrote {num_cards} cards in {duration:.2f} seconds")
    assert duration < 10  # Should complete within 10 seconds

def test_read_performance(repository):
    """Test read performance."""
    # Create test data
    cards = []
    for i in range(1000):
        card = MCard(content=f"Content {i}")
        repository.save(card)
        cards.append(card)
    
    # Test read performance
    start_time = time.time()
    for card in cards:
        retrieved = repository.get(card.hash)
        assert retrieved is not None
    
    duration = time.time() - start_time
    logging.info(f"Read {len(cards)} cards in {duration:.2f} seconds")
    assert duration < 10  # Should complete within 10 seconds

def test_batch_performance(repository):
    """Test batch operation performance."""
    # Create test data
    num_cards = 1000
    cards = [MCard(content=f"Content {i}") for i in range(num_cards)]
    
    # Test batch save
    start_time = time.time()
    repository.save_many(cards)
    save_duration = time.time() - start_time
    logging.info(f"Batch saved {num_cards} cards in {save_duration:.2f} seconds")
    
    # Test batch get
    start_time = time.time()
    hashes = [card.hash for card in cards]
    retrieved_cards = repository.get_many(hashes)
    get_duration = time.time() - start_time
    logging.info(f"Batch retrieved {len(retrieved_cards)} cards in {get_duration:.2f} seconds")
    
    assert save_duration < 5  # Should complete within 5 seconds
    assert get_duration < 5  # Should complete within 5 seconds

def test_concurrent_performance(repository):
    """Test concurrent operation performance."""
    num_threads = 4
    cards_per_thread = 250
    
    def worker(start_idx):
        for i in range(start_idx, start_idx + cards_per_thread):
            card = MCard(content=f"Content {i}")
            repository.save(card)
            retrieved = repository.get(card.hash)
            assert retrieved is not None
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i * cards_per_thread) for i in range(num_threads)]
        concurrent.futures.wait(futures)
    
    duration = time.time() - start_time
    total_operations = num_threads * cards_per_thread * 2  # save + get
    logging.info(f"Completed {total_operations} concurrent operations in {duration:.2f} seconds")
    assert duration < 20  # Should complete within 20 seconds

def test_query_performance(repository):
    """Test query performance."""
    # Create test data
    num_cards = 1000
    for i in range(num_cards):
        card = MCard(content=f"Content {i}")
        repository.save(card)
    
    # Test get_all performance
    start_time = time.time()
    all_cards = repository.get_all()
    duration = time.time() - start_time
    logging.info(f"Retrieved {len(all_cards)} cards in {duration:.2f} seconds")
    assert duration < 5  # Should complete within 5 seconds

def test_delete_performance(repository):
    """Test delete performance."""
    # Create test data
    cards = []
    for i in range(1000):
        card = MCard(content=f"Content {i}")
        repository.save(card)
        cards.append(card)
    
    # Test delete performance
    start_time = time.time()
    for card in cards:
        repository.delete(card.hash)
    
    duration = time.time() - start_time
    logging.info(f"Deleted {len(cards)} cards in {duration:.2f} seconds")
    assert duration < 10  # Should complete within 10 seconds
