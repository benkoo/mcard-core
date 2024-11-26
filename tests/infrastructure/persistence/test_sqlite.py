"""Tests for SQLite card repository."""
import os
import pytest
import asyncio
import tempfile
from datetime import datetime, timezone
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
    os.unlink(temp_path)

@pytest.fixture
def repository(db_path):
    """Fixture for SQLite repository."""
    return SQLiteCardRepository(db_path, pool_size=2)

@pytest.mark.asyncio
async def test_save_and_get_card(repository):
    """Test saving and retrieving a card."""
    content = "Test content"
    card = MCard(content=content)
    
    try:
        await repository.save(card)
        retrieved = await repository.get(card.hash)
        
        assert retrieved is not None
        assert retrieved.hash == card.hash
        assert retrieved.content == content
        assert isinstance(retrieved.g_time, datetime)
        assert retrieved.g_time.tzinfo == timezone.utc
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_get_nonexistent_card(repository):
    """Test retrieving a non-existent card."""
    try:
        retrieved = await repository.get("nonexistent")
        assert retrieved is None
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_save_large_content(repository):
    """Test saving content larger than max size."""
    try:
        large_content = "x" * (repository.max_content_size + 1)
        card = MCard(content=large_content)
        
        with pytest.raises(ValidationError):
            await repository.save(card)
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_get_all_cards(repository):
    """Test retrieving all cards."""
    try:
        cards = [
            MCard(content="Content 1"),
            MCard(content="Content 2"),
            MCard(content="Content 3")
        ]
        
        for card in cards:
            await repository.save(card)
        
        retrieved = await repository.get_all()
        assert len(retrieved) == len(cards)
        retrieved_hashes = {card.hash for card in retrieved}
        original_hashes = {card.hash for card in cards}
        assert retrieved_hashes == original_hashes
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_delete_card(repository):
    """Test deleting a card."""
    try:
        card = MCard(content="Test content")
        await repository.save(card)
        
        # Verify card exists
        assert await repository.get(card.hash) is not None
        
        # Delete card
        await repository.delete(card.hash)
        
        # Verify card is deleted
        assert await repository.get(card.hash) is None
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_delete_nonexistent_card(repository):
    """Test deleting a non-existent card."""
    try:
        # Should not raise an error
        await repository.delete("nonexistent")
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_concurrent_operations(repository):
    """Test concurrent operations on the repository."""
    try:
        async def save_and_get():
            card = MCard(content=f"Content {datetime.now()}")
            await repository.save(card)
            retrieved = await repository.get(card.hash)
            assert retrieved is not None
            assert retrieved.hash == card.hash
            return card
        
        # Run multiple operations concurrently
        tasks = [save_and_get() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        assert len(results) == 5
        assert len({card.hash for card in results}) == 5  # All cards should be unique
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_transaction_rollback(repository):
    """Test transaction rollback on error."""
    try:
        card = MCard(content="Test content")
        
        try:
            async with repository.transaction():
                await repository.save(card)
                # Simulate an error
                raise RuntimeError("Test error")
        except RuntimeError:
            pass
        
        # Card should not be saved due to rollback
        retrieved = await repository.get(card.hash)
        assert retrieved is None
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_save_many_and_get_many(repository):
    """Test batch saving and retrieving cards."""
    try:
        # Create test cards
        cards = [
            MCard(content=f"Content {i}")
            for i in range(5)
        ]
        
        # Save all cards at once
        await repository.save_many(cards)
        
        # Retrieve cards by their hashes
        hashes = [card.hash for card in cards]
        retrieved = await repository.get_many(hashes)
        
        assert len(retrieved) == len(cards)
        retrieved_dict = {card.hash: card for card in retrieved}
        
        for original in cards:
            assert original.hash in retrieved_dict
            retrieved_card = retrieved_dict[original.hash]
            assert retrieved_card.content == original.content
            assert retrieved_card.g_time.tzinfo == timezone.utc
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_get_all_with_pagination(repository):
    """Test retrieving all cards with pagination."""
    try:
        # Create 10 test cards
        cards = [
            MCard(content=f"Content {i}")
            for i in range(10)
        ]
        await repository.save_many(cards)
        
        # Test first page
        page1 = await repository.get_all(limit=5, offset=0)
        assert len(page1) == 5
        
        # Test second page
        page2 = await repository.get_all(limit=5, offset=5)
        assert len(page2) == 5
        
        # Verify no overlap between pages
        page1_hashes = {card.hash for card in page1}
        page2_hashes = {card.hash for card in page2}
        assert not (page1_hashes & page2_hashes)  # No intersection
        
        # Verify we got all cards
        all_hashes = {card.hash for card in cards}
        retrieved_hashes = page1_hashes | page2_hashes
        assert retrieved_hashes == all_hashes
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_binary_content(repository):
    """Test handling binary content."""
    try:
        # Create a card with binary content
        binary_content = bytes([0x00, 0x01, 0x02, 0x03])
        card = MCard(content=binary_content)
        
        await repository.save(card)
        retrieved = await repository.get(card.hash)
        
        assert retrieved is not None
        assert isinstance(retrieved.content, bytes)
        assert retrieved.content == binary_content
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_connection_pool_limit(repository):
    """Test connection pool limit handling."""
    try:
        # Create more concurrent operations than pool size
        async def operation(i):
            card = MCard(content=f"Content {i}")
            await repository.save(card)
            return await repository.get(card.hash)
        
        # Run pool_size + 1 operations
        tasks = [operation(i) for i in range(repository.pool_size + 1)]
        
        # This should work despite exceeding pool size due to connection reuse
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations succeeded
        for result in results:
            assert isinstance(result, MCard)
            assert result.content.startswith("Content ")
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_error_handling(repository):
    """Test error handling for various database operations."""
    try:
        # Test invalid hash format
        with pytest.raises(StorageError):
            await repository.get(None)
        
        # Test invalid content size
        large_card = MCard(content="x" * (repository.max_content_size + 1))
        with pytest.raises(ValidationError):
            await repository.save(large_card)
        
        # Test invalid batch operation
        with pytest.raises(StorageError):
            await repository.get_many([None, None])
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_nested_transactions(repository):
    """Test nested transaction handling."""
    try:
        card1 = MCard(content="Content 1")
        card2 = MCard(content="Content 2")
        
        # Start outer transaction
        async with repository.transaction():
            await repository.save(card1)
            
            # Start inner transaction that fails
            try:
                async with repository.transaction():
                    await repository.save(card2)
                    raise RuntimeError("Inner transaction error")
            except RuntimeError:
                pass
            
            # Card2 should not be saved, but card1 should still be in the outer transaction
            assert await repository.get(card2.hash) is None
            assert await repository.get(card1.hash) is not None
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_mixed_content_batch(repository):
    """Test batch operations with mixed content types."""
    try:
        # Create cards with different content types
        text_content = "Plain text content"
        binary_content = bytes([0x00, 0xFF, 0xAA, 0x55])
        emoji_content = "Hello 👋 World 🌍"
        
        cards = [
            MCard(content=text_content),
            MCard(content=binary_content),
            MCard(content=emoji_content)
        ]
        
        # Save all cards in a batch
        await repository.save_many(cards)
        
        # Retrieve and verify each card
        for original in cards:
            retrieved = await repository.get(original.hash)
            assert retrieved is not None
            assert retrieved.content == original.content
            assert type(retrieved.content) == type(original.content)
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_transaction_isolation(repository):
    """Test transaction isolation between concurrent operations."""
    try:
        async def transaction1():
            async with repository.transaction():
                card = MCard(content="Transaction 1")
                await repository.save(card)
                # Simulate some work
                await asyncio.sleep(0.1)
                return card.hash

        async def transaction2():
            # Try to read the card from transaction1 before it commits
            async with repository.transaction():
                card = MCard(content="Transaction 2")
                await repository.save(card)
                return card.hash

        # Run transactions concurrently
        task1 = asyncio.create_task(transaction1())
        task2 = asyncio.create_task(transaction2())
        
        hash1, hash2 = await asyncio.gather(task1, task2)
        
        # Verify both transactions completed
        card1 = await repository.get(hash1)
        card2 = await repository.get(hash2)
        
        assert card1 is not None
        assert card2 is not None
        assert card1.content == "Transaction 1"
        assert card2.content == "Transaction 2"
    finally:
        await repository.close()

@pytest.mark.asyncio
async def test_connection_error_recovery(repository):
    """Test repository recovery after connection errors."""
    try:
        # First operation should succeed
        card1 = MCard(content="Before error")
        await repository.save(card1)
        
        # Simulate a connection error by closing all connections
        await repository.close()
        
        # Next operation should recover and succeed
        card2 = MCard(content="After error")
        await repository.save(card2)
        
        # Verify both operations succeeded
        retrieved1 = await repository.get(card1.hash)
        retrieved2 = await repository.get(card2.hash)
        
        assert retrieved1 is not None
        assert retrieved2 is not None
        assert retrieved1.content == "Before error"
        assert retrieved2.content == "After error"
    finally:
        await repository.close()
