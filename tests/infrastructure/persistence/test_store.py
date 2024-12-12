"""Test store."""
import os
import pytest
import pytest_asyncio
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.store import MCardStore
from mcard.infrastructure.persistence.database_engine_config import EngineType
from mcard.infrastructure.infrastructure_config_manager import load_config, DataEngineConfig

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_store.log')
    ]
)

logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
async def cleanup_store():
    """Cleanup fixture that runs after each test."""
    yield
    # Force close any remaining connections
    await asyncio.sleep(0.1)  # Allow any pending operations to complete
    
    # Clean up the test database
    try:
        import os
        if os.path.exists("test.db"):
            os.remove("test.db")
    except Exception as e:
        logger.warning(f"Failed to cleanup test database: {e}")

@pytest_asyncio.fixture
async def store():
    """Create a fresh store instance for each test."""
    store_instance = None
    db_path = "test.db"
    try:
        # Create store instance
        store_instance = MCardStore()
        
        # Reset any existing configuration
        await store_instance.reset()
        
        # Configure with SQLite database
        store_instance.configure(
            engine_type=EngineType.SQLITE,
            connection_string=db_path,
            max_connections=5,
            timeout=30.0
        )
        
        # Initialize the store
        await store_instance.initialize()
        
        # Run the test
        yield store_instance
        
    except Exception as e:
        logger.error(f"Error setting up store: {e}")
        raise
    finally:
        # Clean up
        if store_instance:
            try:
                await store_instance.close()
                await store_instance.reset()
            except Exception as e:
                logger.warning(f"Failed to close store: {e}")
            finally:
                try:
                    if os.path.exists(db_path):
                        os.remove(db_path)
                except Exception as e:
                    logger.warning(f"Failed to remove database file: {e}")

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

@pytest.fixture
def sample_binary_content() -> List[bytes]:
    """Fixture providing various binary content for testing."""
    return [
        bytes([0x00, 0x01, 0x02, 0x03]),  # Simple binary
        bytes([i for i in range(256)]),    # Full byte range
        b"\x00\xFF" * 1000,               # Repeating pattern
        os.urandom(1024)                  # Random binary
    ]

@pytest.fixture
def sample_text_content() -> List[str]:
    """Fixture providing various text content for testing."""
    return [
        "",                                # Empty string
        "Hello, World!",                   # ASCII
        "Hello 你好 👋 🌍",                 # Unicode with emojis
        "\\x00\\xff",                      # Escaped binary
        "Line 1\nLine 2\r\nLine 3",        # Different line endings
        "\t\n\r\f\v",                      # Whitespace characters
        "a" * 10000                        # Large text
    ]

def create_sample_webp(width=100, height=100, **kwargs) -> bytes:
    """Create a sample WebP image for testing."""
    image = Image.new('RGB', (width, height))
    pixels = image.load()
    for i in range(width):
        for j in range(height):
            pixels[i,j] = (i % 256, j % 256, (i + j) % 256)
    
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", **kwargs)
    return buffer.getvalue()

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
    try:
        # Create a test card with unique content
        test_card = MCard(
            content=f"Test content {uuid.uuid4()}",  # Ensure unique content
            hash=None,  # Let the store compute the hash
            g_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Test save and retrieve
        await store.save(test_card)
        assert test_card.hash is not None, "Hash should be computed after save"
        
        retrieved_card = await store.get(test_card.hash)
        assert retrieved_card is not None, "Card should exist after save"
        assert retrieved_card.content == test_card.content
        assert retrieved_card.hash == test_card.hash
        assert retrieved_card.g_time == test_card.g_time
        
        # Test delete
        await store.delete(test_card.hash)
        deleted_card = await store.get(test_card.hash)
        assert deleted_card is None, "Card should not exist after delete"
        
    except Exception as e:
        logger.error(f"Error in card operations test: {e}")
        raise

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
async def test_error_handling(store):
    """Test error handling in the store."""
    # Test operations on unconfigured store
    unconfigured_store = MCardStore()
    await unconfigured_store.reset()  # Reset to ensure it's unconfigured
    with pytest.raises(StorageError, match="Store not configured"):
        await unconfigured_store.get("any_hash")
    
    # Test save with invalid content
    with pytest.raises(ValidationError, match="Card content cannot be None"):
        await store.save(MCard(content=None))
    
    # Test save_many with invalid cards
    with pytest.raises(ValidationError, match="Card content cannot be None"):
        await store.save_many([MCard(content=None), MCard(content="valid")])
    
    # Test operations with None values
    with pytest.raises(ValueError):
        await store.get(None)
    
    with pytest.raises(ValueError):
        await store.delete(None)

@pytest.mark.asyncio
async def test_connection_isolation():
    """Test connection isolation between store instances."""
    # Create first store
    store1 = MCardStore()
    await store1.reset()
    store1.configure(
        engine_type=EngineType.SQLITE,
        connection_string="test_isolation.db"
    )
    await store1.initialize()
    
    # Create second store
    store2 = MCardStore()
    await store2.reset()
    store2.configure(
        engine_type=EngineType.SQLITE,
        connection_string="test_isolation.db"
    )
    await store2.initialize()
    
    try:
        # Create and save a card in first store
        card1 = MCard(content="Test content 1")
        await store1.save(card1)
        
        # Verify second store can see the card
        retrieved1 = await store2.get(card1.hash)
        assert retrieved1 is not None
        assert retrieved1.content == card1.content
        
        # Create and save a card in second store
        card2 = MCard(content="Test content 2")
        await store2.save(card2)
        
        # Verify first store can see the card
        retrieved2 = await store1.get(card2.hash)
        assert retrieved2 is not None
        assert retrieved2.content == card2.content
        
        # Test concurrent modifications
        card3 = MCard(content="Test content 3")
        card4 = MCard(content="Test content 4")
        
        await asyncio.gather(
            store1.save(card3),
            store2.save(card4)
        )
        
        # Verify both stores can see all cards
        assert (await store1.get(card3.hash)) is not None
        assert (await store1.get(card4.hash)) is not None
        assert (await store2.get(card3.hash)) is not None
        assert (await store2.get(card4.hash)) is not None
        
    finally:
        # Cleanup
        try:
            await store1.close()
            await store2.close()
        except Exception as e:
            logger.warning(f"Error during store cleanup: {e}")
        finally:
            # Remove test database
            try:
                if os.path.exists("test_isolation.db"):
                    os.remove("test_isolation.db")
            except Exception as e:
                logger.warning(f"Error removing test database: {e}")

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

@pytest.mark.asyncio
async def test_connection_recovery(store):
    """Test that the store can recover from connection issues."""
    try:
        # Create and save a test card
        test_card = MCard(content="Test content")
        await store.save(test_card)
        
        # Force close all connections
        await store.close()
        
        # Try to get the card - should reconnect automatically
        retrieved_card = await store.get(test_card.hash)
        assert retrieved_card is not None
        assert retrieved_card.content == test_card.content
        
        # Test multiple operations after recovery
        test_card2 = MCard(content="Test content 2")
        await store.save(test_card2)
        
        retrieved_cards = await asyncio.gather(
            store.get(test_card.hash),
            store.get(test_card2.hash)
        )
        assert all(card is not None for card in retrieved_cards)
        
    except Exception as e:
        logger.error(f"Error in connection recovery test: {e}")
        raise

@pytest.mark.asyncio
async def test_concurrent_operations(store):
    """Test concurrent operations on the store."""
    num_cards = 5
    cards = [MCard(content=f"Test content {i}") for i in range(num_cards)]
    
    async def save_and_get(card):
        await store.save(card)
        retrieved = await store.get(card.hash)
        assert retrieved is not None
        assert retrieved.content == card.content
        return retrieved
    
    try:
        # Create tasks for concurrent operations
        tasks = [asyncio.create_task(save_and_get(card)) for card in cards]
        
        # Use wait_for to prevent hanging
        async with asyncio.timeout(10.0):
            results = await asyncio.gather(*tasks)
            
        # Verify results
        assert len(results) == num_cards
        for i, result in enumerate(results):
            assert result.content == f"Test content {i}"
            
    except TimeoutError:
        pytest.fail("Concurrent operations timed out after 10 seconds")
    except Exception as e:
        pytest.fail(f"Concurrent operations failed: {e}")
    finally:
        # Ensure all tasks are cleaned up
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

@pytest.mark.asyncio
async def test_concurrent_read_operations(store):
    """Test concurrent read operations."""
    # Create test data
    cards = []
    for i in range(10):
        card = MCard(content=f"Content {i}")
        await store.save(card)
        cards.append(card)

    async def read_card(card_hash: str) -> MCard:
        retrieved = await store.get(card_hash)
        assert retrieved is not None
        return retrieved

    # Test concurrent reads
    tasks = [read_card(card.hash) for card in cards]
    results = await asyncio.gather(*tasks)

    assert len(results) == len(cards)
    assert all(isinstance(card, MCard) for card in results)
    assert all(card.content == f"Content {i}" for i, card in enumerate(results))

@pytest.mark.asyncio
async def test_concurrent_write_operations(store):
    """Test concurrent write operations."""
    async def save_card(content: str) -> str:
        card = MCard(content=content)
        await store.save(card)
        return card.hash

    # Test concurrent writes with retry on lock
    tasks = []
    for i in range(5):
        tasks.append(save_card(f"Concurrent content {i}"))

    try:
        card_hashes = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10.0)
    except asyncio.TimeoutError:
        pytest.fail("Concurrent write operations timed out")

    # Verify all cards were saved
    all_saved = True
    for hash_value in card_hashes:
        retrieved = await store.get(hash_value)
        all_saved = all_saved and retrieved is not None

    assert all_saved, "Not all cards were saved successfully"

@pytest.mark.asyncio
async def test_binary_content_handling(store, sample_binary_content):
    """Test handling of binary content."""
    for content in sample_binary_content:
        # Ensure content is bytes
        if not isinstance(content, bytes):
            content = bytes(content)
            
        card = MCard(content=content)
        await store.save(card)
        retrieved = await store.get(card.hash)
        
        assert retrieved is not None
        retrieved_content = retrieved.content
        
        # If content is returned as string, convert it back to bytes
        if isinstance(retrieved_content, str):
            # Handle escaped byte string
            if retrieved_content.startswith('\\x'):
                # Remove '\\x' prefix and convert to bytes
                hex_str = retrieved_content.replace('\\x', '')
                retrieved_content = bytes.fromhex(hex_str)
            else:
                # Handle regular string to bytes conversion
                retrieved_content = retrieved_content.encode('utf-8')
        
        assert isinstance(retrieved_content, bytes)
        assert retrieved_content == content

@pytest.mark.asyncio
async def test_text_content_handling(store, sample_text_content):
    """Test handling of text content."""
    for content in sample_text_content:
        card = MCard(content=content)
        await store.save(card)
        retrieved = await store.get(card.hash)
        
        assert retrieved is not None
        assert isinstance(retrieved.content, str)
        assert retrieved.content == content

@pytest.mark.asyncio
async def test_webp_content_handling(store):
    """Test handling of WebP image content."""
    # Test different WebP configurations
    webp_contents = [
        create_sample_webp(quality=50),                    # Lossy
        create_sample_webp(lossless=True),                 # Lossless
        create_sample_webp(width=1920, height=1080),       # Large resolution
        create_sample_webp(width=50, height=50)            # Small resolution
    ]

    for content in webp_contents:
        card = MCard(content=content)
        await store.save(card)
        retrieved = await store.get(card.hash)
        
        assert retrieved is not None
        assert isinstance(retrieved.content, bytes)
        assert retrieved.content == content
        
        # Verify it's still valid WebP
        img = Image.open(io.BytesIO(retrieved.content))
        assert img.format == 'WEBP'

@pytest.mark.asyncio
async def test_content_size_limits(store):
    """Test content size limits and error handling."""
    # Test with increasingly large content
    sizes = [1024, 1024*1024, 10*1024*1024]
    
    for size in sizes:
        content = os.urandom(size)
        card = MCard(content=content)
        
        try:
            await store.save(card)
            retrieved = await store.get(card.hash)
            assert retrieved is not None
            assert len(retrieved.content) == size
        except StorageError as e:
            logger.info(f"Size {size} exceeded limit: {e}")
            # If we hit a limit, verify it's enforced consistently
            with pytest.raises(StorageError):
                await store.save(card)

@pytest.mark.asyncio
async def test_content_updates(store):
    """Test updating content of existing cards."""
    # Create initial card
    initial_content = "Initial content"
    card = MCard(content=initial_content)
    await store.save(card)
    
    # Update scenarios to test
    update_scenarios = [
        "Updated content",                          # Simple update
        "Updated with unicode: 你好 👋",            # Unicode update
        "a" * 1000,                                # Large update
        "",                                        # Empty content
        "\\x00\\x01\\x02\\x03",                   # Binary-like content
    ]
    
    for new_content in update_scenarios:
        # Create new card with same hash
        updated_card = MCard(content=new_content)  # Let it generate new hash
        await store.save(updated_card)
        
        # Verify update
        retrieved = await store.get(updated_card.hash)
        assert retrieved is not None
        assert retrieved.content == new_content

@pytest.mark.asyncio
async def test_read_write_isolation(store):
    """Test isolation between concurrent reads and writes."""
    # Initial setup
    initial_cards = []
    initial_hashes = []
    
    for i in range(5):
        card = MCard(content=f"Initial {i}")
        await store.save(card)
        initial_cards.append(card)
        initial_hashes.append(card.hash)
    
    # Track read results
    read_results = []
    write_complete = asyncio.Event()
    read_complete = asyncio.Event()
    
    async def reader():
        try:
            while not write_complete.is_set():
                # Check each initial card
                valid_reads = 0
                for hash_value in initial_hashes:
                    try:
                        if await store.get(hash_value) is not None:
                            valid_reads += 1
                    except StorageError:
                        # Ignore storage errors during concurrent operations
                        pass
                read_results.append(valid_reads)
                await asyncio.sleep(0.01)
            read_complete.set()
        except asyncio.CancelledError:
            read_complete.set()
            raise
    
    async def writer():
        try:
            for i in range(5):
                card = MCard(content=f"Additional {i}")
                await store.save(card)
                initial_hashes.append(card.hash)
                await asyncio.sleep(0.02)
            write_complete.set()
        except Exception:
            write_complete.set()
            raise
    
    # Run reader and writer concurrently
    reader_task = asyncio.create_task(reader())
    writer_task = asyncio.create_task(writer())
    
    try:
        # Wait for writer to complete first
        await asyncio.wait_for(writer_task, timeout=5.0)
        # Then wait for reader to notice and complete
        await asyncio.wait_for(read_complete.wait(), timeout=1.0)
    except asyncio.TimeoutError:
        write_complete.set()
        await asyncio.sleep(0.1)  # Give tasks a chance to clean up
    finally:
        # Clean up tasks
        if not reader_task.done():
            reader_task.cancel()
            try:
                await reader_task
            except (asyncio.CancelledError, StorageError):
                pass
        if not writer_task.done():
            writer_task.cancel()
            try:
                await writer_task
            except (asyncio.CancelledError, StorageError):
                pass
    
    # Verify results - check all hashes exist
    all_exist = True
    for hash_value in initial_hashes:
        try:
            if await store.get(hash_value) is None:
                all_exist = False
                break
        except StorageError:
            all_exist = False
            break
    
    assert all_exist, "Some cards are missing after concurrent operations"
    assert len(read_results) > 0, "No reads were completed"
    assert all(count >= 5 for count in read_results), "Saw inconsistent state during reads"

@pytest.mark.asyncio
async def test_transaction_rollback(store):
    """Test transaction rollback under error conditions."""
    try:
        # Create initial card
        initial_card = MCard(content="Initial content")
        await store.save(initial_card)
        initial_hash = initial_card.hash
        
        # Try to save a card with the same hash (should fail)
        duplicate_card = MCard(content="Different content")
        duplicate_card._hash = initial_hash
        
        with pytest.raises(StorageError):
            await store.save(duplicate_card)
        
        # Verify original content was preserved
        retrieved = await store.get(initial_hash)
        assert retrieved is not None
        assert retrieved.content == "Initial content"
        
        # Try concurrent duplicate saves
        cards = []
        for i in range(3):
            card = MCard(content=f"Content {i}")
            card._hash = initial_hash
            cards.append(card)
        
        # Try to save them all at once (should fail)
        with pytest.raises(StorageError):
            async with asyncio.timeout(5.0):
                await asyncio.gather(*[store.save(card) for card in cards])
        
        # Verify database state is still consistent
        retrieved = await store.get(initial_hash)
        assert retrieved is not None
        assert retrieved.content == "Initial content"
    finally:
        # Ensure connections are cleaned up
        await asyncio.sleep(0.1)
