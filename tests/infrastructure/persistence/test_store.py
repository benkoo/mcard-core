"""Tests for the MCardStore singleton class."""

import os
import pytest
import pytest_asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.store import MCardStore
from mcard.infrastructure.persistence.engine_config import EngineType
from mcard.infrastructure.config import load_config

@pytest_asyncio.fixture
async def store():
    """Create and configure a test store instance."""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Create and configure store
    store = MCardStore()
    await store.reset()  # Reset any previous configuration
    store.configure(
        engine_type=EngineType.SQLITE,
        connection_string=db_path
    )
    
    # Initialize store
    await store.initialize()
    
    try:
        yield store
    finally:
        # Cleanup
        await store.close()
        await store.reset()  # Reset for next test
        if os.path.exists(db_path):
            os.unlink(db_path)

@pytest.fixture
def test_cards() -> List[MCard]:
    """Fixture that provides a list of test cards."""
    return [
        MCard(
            content=f"Test content {i}",
            hash=None,  # Let the store compute the hash
            g_time=datetime.now(timezone.utc).isoformat()
        )
        for i in range(5)
    ]

@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test that MCardStore follows the singleton pattern."""
    store1 = MCardStore()
    store2 = MCardStore()
    assert store1 is store2

@pytest.mark.asyncio
async def test_store_configuration():
    """Test store configuration and reconfiguration."""
    store = MCardStore()
    
    # Test default configuration
    store.configure()
    assert store.is_configured
    assert store.config.engine_config.engine_type == EngineType.SQLITE
    default_path = str(Path.home() / ".mcard" / "storage.db")
    assert store.config.engine_config.connection_string == default_path

    # Test reset and reconfigure
    await store.reset()
    assert not store.is_configured
    
    # Test custom configuration
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        store.configure(
            engine_type=EngineType.SQLITE,
            connection_string=f.name,
            max_connections=5,
            timeout=30.0
        )
        assert store.is_configured
        assert store.config.engine_config.engine_type == EngineType.SQLITE
        assert store.config.engine_config.connection_string == f.name
        assert store.config.engine_config.max_connections == 5

    # Test reconfiguration error
    with pytest.raises(RuntimeError, match="Store is already configured"):
        store.configure()

@pytest.mark.asyncio
async def test_card_operations(store):
    """Test basic card operations using the store."""
    # Create a test card
    test_card = MCard(
        content="Test content",
        hash=None,  # Let the store compute the hash
        g_time=datetime.now(timezone.utc).isoformat()
    )
    
    # Test save and retrieve
    await store.save(test_card)
    retrieved_card = await store.get(test_card.hash)
    assert retrieved_card.content == test_card.content
    assert retrieved_card.hash == test_card.hash
    
    # Test delete
    await store.delete(test_card.hash)
    deleted_card = await store.get(test_card.hash)
    assert deleted_card is None

@pytest.mark.asyncio
async def test_batch_operations(store, test_cards):
    """Test batch operations using the store."""
    # Test save_many
    await store.save_many(test_cards)
    
    # Test retrieval of all cards
    for card in test_cards:
        retrieved = await store.get(card.hash)
        assert retrieved is not None
        assert retrieved.content == card.content

def test_hash_computation(store):
    """Test hash computation using the configured hashing service."""
    content = "Test content"
    
    # Test with default hash settings
    hash1 = store.compute_hash(content.encode('utf-8'))
    hash2 = store.compute_hash(content.encode('utf-8'))
    
    assert hash1 == hash2  # Same content should produce same hash
    assert isinstance(hash1, str)  # Hash should be a string

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in the store."""
    store = MCardStore()
    
    # Test operations without configuration
    with pytest.raises(StorageError, match="Store not configured"):
        await store.save(MCard(content="test", hash=None))

@pytest.mark.asyncio
async def test_store_initialization():
    """Test store initialization and schema creation."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    store = MCardStore()
    await store.reset()  # Ensure clean state
    store.configure(
        engine_type=EngineType.SQLITE,
        connection_string=db_path
    )

    try:
        # Test initialization
        await store.initialize()
        assert store.is_configured
        assert os.path.exists(db_path)

        # Test that we can perform operations on the initialized database
        test_card = MCard(
            content="Test initialization",
            hash=None,
            g_time=datetime.now(timezone.utc).isoformat()
        )
        await store.save(test_card)
        
        # Verify we can retrieve the card
        retrieved_card = await store.get(test_card.hash)
        assert retrieved_card is not None
        assert retrieved_card.content == test_card.content
    finally:
        await store.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
