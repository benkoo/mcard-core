"""Performance tests for MCardStore."""
import pytest
import tempfile
import os
import time
import asyncio
from datetime import datetime, timezone
from mcard.infrastructure.persistence.store import MCardStore
from mcard.infrastructure.persistence.database_engine_config import EngineType
from mcard.infrastructure.infrastructure_config_manager import DataEngineConfig, load_config
from mcard.domain.models.card import MCard
import logging
import pytest_asyncio

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

@pytest_asyncio.fixture
async def store(db_path):
    """Fixture for MCardStore."""
    store = MCardStore()
    store.configure(
        engine_type=EngineType.SQLITE,
        connection_string=db_path,
        timeout=5.0
    )
    await store.initialize()  # Ensure store is initialized
    try:
        yield store
    finally:
        await store.reset()

@pytest.mark.asyncio
async def test_write_performance(store):
    """Test write performance."""
    start_time = time.time()
    num_cards = 1000
    
    for i in range(num_cards):
        card = MCard(content=f"Content {i}")
        await store.save(card)
    
    duration = time.time() - start_time
    logging.info(f"Wrote {num_cards} cards in {duration:.2f} seconds")
    assert duration < 10  # Should complete within 10 seconds

@pytest.mark.asyncio
async def test_read_performance(store):
    """Test read performance."""
    # Create test data
    cards = []
    for i in range(1000):
        card = MCard(content=f"Content {i}")
        await store.save(card)
        cards.append(card)
    
    # Test read performance
    start_time = time.time()
    for card in cards:
        retrieved = await store.get(card.hash)
        assert retrieved is not None
        assert retrieved.content == card.content
    
    duration = time.time() - start_time
    logging.info(f"Read {len(cards)} cards in {duration:.2f} seconds")
    assert duration < 10  # Should complete within 10 seconds

@pytest.mark.asyncio
async def test_concurrent_performance(store):
    """Test concurrent operation performance."""
    num_tasks = 4
    cards_per_task = 250
    
    async def worker(start_idx):
        for i in range(start_idx, start_idx + cards_per_task):
            card = MCard(content=f"Content {i}")
            await store.save(card)
            retrieved = await store.get(card.hash)
            assert retrieved is not None
            assert retrieved.content == card.content
    
    start_time = time.time()
    tasks = [worker(i * cards_per_task) for i in range(num_tasks)]
    await asyncio.gather(*tasks)
    duration = time.time() - start_time
    
    logging.info(f"Processed {num_tasks * cards_per_task} concurrent operations in {duration:.2f} seconds")
    assert duration < 20  # Should complete within 20 seconds

@pytest.mark.asyncio
async def test_content_type_performance(store):
    """Test performance with different content types."""
    num_cards = 100
    content_types = ['text/plain', 'image/webp', 'application/json']
    
    for idx, content_type in enumerate(content_types):
        # Create test data
        start_time = time.time()
        cards = []
        for i in range(num_cards):
            # Add content type prefix to make content unique across types
            content = f"{content_type}:Content {i}" if content_type == 'text/plain' else f"{content_type}:Binary content {i}"
            card = MCard(content=content)
            await store.save(card)
            cards.append(card)
            
            # Verify immediately
            retrieved = await store.get(card.hash)
            assert retrieved is not None
            assert retrieved.content == card.content
        
        duration = time.time() - start_time
        logging.info(f"Processed {num_cards} {content_type} cards in {duration:.2f} seconds")
        assert duration < 10  # Should complete within 10 seconds

@pytest.mark.asyncio
async def test_large_content_performance(store):
    """Test performance with large content."""
    sizes = [1024, 10*1024, 100*1024]  # Test with 1KB, 10KB, and 100KB content
    num_cards = 10
    
    for size in sizes:
        start_time = time.time()
        
        # Save cards
        cards = []
        for i in range(num_cards):
            # Create unique content for each card
            content = bytes([j % 256 for j in range(size)]) + bytes([i])  # Add index to make content unique
            card = MCard(content=content)
            await store.save(card)
            cards.append(card)
        
        # Verify retrieval
        for card in cards:
            retrieved = await store.get(card.hash)
            assert retrieved is not None
            assert len(retrieved.content) == size + 1  # +1 for the index byte
        
        duration = time.time() - start_time
        logging.info(f"Processed {num_cards} cards of {size/1024:.1f}KB each in {duration:.2f} seconds")
        assert duration < 10  # Should complete within 10 seconds
