"""Advanced tests for SQLite card repository covering edge cases and performance."""
import os
import time
import pytest
import asyncio
import tempfile
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError, ValidationError

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
    return SQLiteCardRepository(db_path, pool_size=2)

@pytest.mark.asyncio
async def test_concurrent_transactions(db_path):
    """Test handling of concurrent transactions."""
    repo = SQLiteCardRepository(db_path)
    try:
        # Create cards with known content
        cards = [
            MCard(content=f"content_{i}")
            for i in range(10)
        ]
        
        # Save cards concurrently
        await asyncio.gather(*[repo.save(card) for card in cards])
        
        # Verify all cards were saved
        saved_cards = []
        for card in cards:
            saved = await repo.get(card.hash)
            assert saved is not None
            saved_cards.append(saved)
        
        # Verify content matches
        for original, saved in zip(cards, saved_cards):
            assert original.content == saved.content
            assert original.hash == saved.hash
    finally:
        await repo.close()

@pytest.mark.asyncio
async def test_large_content_handling(db_path):
    """Test handling of content near size limits."""
    repo = SQLiteCardRepository(db_path)
    try:
        # Test content just under the limit
        content_size = repo.max_content_size - 1024  # 1KB under limit
        content = b"x" * content_size
        card = MCard(content=content)
        await repo.save(card)
        
        # Verify large content was saved correctly
        saved = await repo.get(card.hash)
        assert saved is not None
        assert len(saved.content) == content_size
        
        # Test content over the limit
        with pytest.raises(ValidationError):
            oversized = b"x" * (repo.max_content_size + 1)
            card = MCard(content=oversized)
            await repo.save(card)
    finally:
        await repo.close()

@pytest.mark.asyncio
async def test_connection_pool_management(db_path):
    """Test connection pool management."""
    repo = SQLiteCardRepository(db_path, pool_size=2)
    try:
        # Verify we can use up to pool_size connections
        async def concurrent_operation(i):
            card = MCard(content=f"content_{i}")
            await repo.save(card)
            saved = await repo.get(card.hash)
            assert saved is not None
            assert saved.content == f"content_{i}"
        
        # This should work with pool_size=2
        await asyncio.gather(*[
            concurrent_operation(i) 
            for i in range(2)
        ])
    finally:
        await repo.close()

@pytest.mark.asyncio
async def test_binary_and_text_content(db_path):
    """Test handling of mixed binary and text content."""
    repo = SQLiteCardRepository(db_path)
    try:
        # Test various content types
        test_cases = [
            ("plain text", str),
            (b"binary\x00data", bytes),
            ("unicode: 🚀", str),
            (b"\x00\x01\x02\x03", bytes),
            ("mixed\ntext\nlines", str),
        ]
        
        for content, expected_type in test_cases:
            card = MCard(content=content)
            await repo.save(card)
            
            saved = await repo.get(card.hash)
            assert saved is not None
            if expected_type == str:
                assert isinstance(saved.content, str)
                if isinstance(content, str):
                    assert saved.content == content
            else:
                assert isinstance(saved.content, (str, bytes))
                if isinstance(content, bytes):
                    assert saved.content.encode('utf-8') == content if isinstance(saved.content, str) else saved.content == content
    finally:
        await repo.close()

@pytest.mark.asyncio
async def test_write_performance(db_path):
    """Benchmark write performance."""
    repo = SQLiteCardRepository(db_path)
    try:
        batch_sizes = [10, 100, 1000]
        results = {}
        
        for size in batch_sizes:
            cards = [MCard(content=f"content_{i}") for i in range(size)]
            start_time = time.time()
            await asyncio.gather(*[repo.save(card) for card in cards])
            end_time = time.time()
            
            results[size] = end_time - start_time
            
        # Verify performance meets requirements
        assert results[1000] < 5.0  # Should complete 1000 writes under 5 seconds
    finally:
        await repo.close()

@pytest.mark.asyncio
async def test_read_performance(db_path):
    """Benchmark read performance."""
    repo = SQLiteCardRepository(db_path)
    try:
        # Setup test data
        cards = [MCard(content=f"content_{i}") for i in range(1000)]
        await asyncio.gather(*[repo.save(card) for card in cards])
        
        # Benchmark random reads
        start_time = time.time()
        for card in cards[:100]:  # Test with 100 random reads
            await repo.get(card.hash)
        end_time = time.time()
        
        read_time = end_time - start_time
        assert read_time < 1.0  # 100 reads should complete under 1 second
    finally:
        await repo.close()

@pytest.mark.asyncio
async def test_error_handling(db_path):
    """Test error handling for various edge cases."""
    repo = SQLiteCardRepository(db_path)
    try:
        # Test invalid hash type
        with pytest.raises(StorageError):
            await repo.get(123)  # type: ignore
        
        # Test getting non-existent hash
        assert await repo.get("nonexistent") is None
        
        # Test saving invalid content type
        with pytest.raises((StorageError, TypeError)):
            card = MCard(content={"invalid": "type"})  # type: ignore
            await repo.save(card)
        
        # Test saving None content
        with pytest.raises((StorageError, TypeError, AttributeError)):
            card = MCard(content=None)  # type: ignore
            await repo.save(card)
    finally:
        await repo.close()
