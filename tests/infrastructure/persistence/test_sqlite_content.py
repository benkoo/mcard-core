"""Tests for content handling in SQLite card store."""
import pytest
import pytest_asyncio
import logging
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
import tempfile
import os
from PIL import Image
import io
import uuid
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test.log')
    ]
)

def create_sample_webp(width=100, height=100, **kwargs):
    """Create a sample WebP image for testing."""
    # Create a new image with a gradient
    image = Image.new('RGB', (width, height))
    pixels = image.load()
    for i in range(width):
        for j in range(height):
            pixels[i,j] = (i % 256, j % 256, (i + j) % 256)
    
    # Convert to WebP
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", **kwargs)
    return buffer.getvalue()

@pytest.fixture
async def db_path():
    """Fixture for temporary database path."""
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
async def repository(db_path):
    """Fixture for SQLite repository."""
    repo = SQLiteStore(SQLiteConfig(db_path=db_path))
    yield repo
    await repo.close()

@pytest.mark.asyncio
async def test_binary_content(repository):
    """Test handling of binary content."""
    test_cases = [
        bytes([0x00, 0x01, 0x02, 0x03]),  # Simple binary
        bytes([i for i in range(256)]),    # Full byte range
        b"\x00\xFF" * 1000,               # Repeating pattern
        os.urandom(1024)                  # Random binary
    ]
    
    for content in test_cases:
        card = MCard(content=content)
        await repository.save(card)
        retrieved = await repository.get(card.hash)
        
        assert retrieved is not None
        assert isinstance(retrieved.content, bytes)
        assert retrieved.content == content

@pytest.mark.asyncio
async def test_text_content(repository):
    """Test handling of text content."""
    test_cases = [
        "",                                # Empty string
        "Hello, World!",                   # ASCII
        "Hello 你好 👋 🌍",                 # Unicode with emojis
        "\\x00\\xff",                      # Escaped binary
        "Line 1\nLine 2\r\nLine 3",        # Different line endings
        "\t\n\r\f\v",                      # Whitespace characters
        "a" * 1000000                      # Large text
    ]
    
    for content in test_cases:
        card = MCard(content=content)
        await repository.save(card)
        retrieved = await repository.get(card.hash)
        
        assert retrieved is not None
        assert isinstance(retrieved.content, str)
        assert retrieved.content == content

@pytest.mark.asyncio
async def test_content_limits(db_path):
    """Test content size limits."""
    # Test with different size limits
    size_limits = [1024, 1024*1024, 10*1024*1024]
    
    for max_size in size_limits:
        config = SQLiteConfig(db_path=db_path, max_content_size=max_size)
        repo = SQLiteStore(config)
        
        # Test content just under limit
        content = b"x" * (max_size - 1)
        card = MCard(content=content)
        await repo.save(card)
        retrieved = await repo.get(card.hash)
        assert retrieved.content == content
        
        # Test content at limit
        content = b"x" * max_size
        card = MCard(content=content)
        await repo.save(card)
        retrieved = await repo.get(card.hash)
        assert retrieved.content == content
        
        # Test content over limit
        content = b"x" * (max_size + 1)
        card = MCard(content=content)
        with pytest.raises(StorageError):
            await repo.save(card)

@pytest.mark.asyncio
async def test_content_updates(repository):
    """Test updating content."""
    # Create initial card
    card = MCard(content="Initial content")
    await repository.save(card)
    card_hash = card.hash
    
    # Update with different content types
    updates = [
        "Updated text",
        "你好 World",
        b"Binary update",
        "Special\x00Chars",
        "a" * 1000  # Smaller update to avoid size limit
    ]
    
    for new_content in updates:
        # Delete existing card
        await repository.delete(card_hash)
        # Create new card with same hash
        updated_card = MCard(content=new_content, hash=card_hash)
        await repository.save(updated_card)
        retrieved = await repository.get(card_hash)
        
        assert retrieved is not None
        assert retrieved.content == new_content

@pytest.mark.asyncio
async def test_special_content(repository):
    """Test handling of special content types."""
    test_cases = [
        # JSON-like content
        '{"key": "value", "numbers": [1,2,3]}',
        
        # XML-like content
        '<root><child>value</child></root>',
        
        # SQL-like content
        'SELECT * FROM table WHERE column = "value"',
        
        # Path-like content
        '/path/to/file.txt',
        'C:\\Windows\\System32',
        
        # URL-like content
        'https://example.com/path?param=value',
        
        # Base64-like content
        'SGVsbG8gV29ybGQ=',
        
        # Mixed content
        'Regular text 123\n<tag>你好</tag>\n{"key": "🌍"}'
    ]
    
    for content in test_cases:
        card = MCard(content=content)
        await repository.save(card)
        retrieved = await repository.get(card.hash)
        
        assert retrieved is not None
        assert retrieved.content == content

@pytest.mark.asyncio
async def test_content_encoding(repository):
    """Test content encoding edge cases."""
    test_cases = [
        # NULL bytes in different positions
        "Start\x00Middle",
        "\x00Start",
        "End\x00",
        
        # Mixed encodings
        "ASCII and 你好 and 🌍",
        
        # RTL text
        "Hello مرحبا שָׁלוֹם",
        
        # Special Unicode
        "".join(chr(i) for i in range(0x20, 0x7F)),  # Printable ASCII
        "".join(chr(i) for i in range(0x1F600, 0x1F620)),  # Emoji range
        
        # Control characters
        "".join(chr(i) for i in range(32)) + "Hello" + "".join(chr(i) for i in range(127, 160))
    ]
    
    for content in test_cases:
        card = MCard(content=content)
        await repository.save(card)
        retrieved = await repository.get(card.hash)
        
        assert retrieved is not None
        assert retrieved.content == content

@pytest.mark.asyncio
async def test_webp_content(repository):
    """Test handling of WebP image content."""
    # Test different WebP sizes and configurations
    test_cases = [
        (100, 100),    # Small image
        (800, 600),    # Medium image
        (1920, 1080),  # Full HD
        (50, 200),     # Non-square aspect ratio
    ]
    
    for width, height in test_cases:
        # Create WebP content
        webp_content = create_sample_webp(width, height)
        
        # Save to repository
        card = MCard(content=webp_content)
        await repository.save(card)
        
        # Retrieve and verify
        retrieved = await repository.get(card.hash)
        assert retrieved is not None
        assert isinstance(retrieved.content, bytes)
        assert len(retrieved.content) > 0
        
        # Verify it's still a valid WebP
        img = Image.open(io.BytesIO(retrieved.content))
        assert img.format == "WEBP"
        assert img.size == (width, height)

@pytest.mark.asyncio
async def test_webp_with_metadata(repository):
    """Test WebP images with metadata."""
    # Create base image
    image = Image.new('RGB', (100, 100))
    
    # Add metadata using exif
    exif = image.getexif()
    exif[0x9286] = "Test Image"  # UserComment
    exif[0x9c9b] = "Test Suite"  # Windows Author
    
    # Save with metadata
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", exif=exif)
    webp_content = buffer.getvalue()
    
    # Save to repository
    card = MCard(content=webp_content)
    await repository.save(card)
    
    # Retrieve and verify
    retrieved = await repository.get(card.hash)
    assert retrieved is not None
    
    # Verify content and metadata preserved
    img = Image.open(io.BytesIO(retrieved.content))
    assert img.format == "WEBP"
    retrieved_exif = img.getexif()
    assert retrieved_exif[0x9286] == "Test Image"
    assert retrieved_exif[0x9c9b] == "Test Suite"

@pytest.mark.asyncio
async def test_webp_compression_modes(repository):
    """Test WebP images with different compression modes."""
    image = Image.new('RGB', (200, 200))
    
    # Test different compression settings
    quality_levels = [0, 50, 100]  # Min, medium, max quality
    lossless_modes = [True, False]
    
    for quality in quality_levels:
        for lossless in lossless_modes:
            buffer = io.BytesIO()
            image.save(buffer, format="WEBP", quality=quality, lossless=lossless)
            webp_content = buffer.getvalue()
            
            # Save to repository with unique hash
            card = MCard(content=webp_content, hash=str(uuid.uuid4()))
            await repository.save(card)
            
            # Retrieve and verify
            retrieved = await repository.get(card.hash)
            assert retrieved is not None
            assert retrieved.content == webp_content
            
            # Verify it's still a valid WebP
            img = Image.open(io.BytesIO(retrieved.content))
            assert img.format == "WEBP"

@pytest.mark.asyncio
async def test_webp_animation(repository):
    """Test animated WebP images."""
    # Create a simple animated WebP
    frames = []
    durations = []
    
    # Create 5 frames with different colors
    for i in range(5):
        frame = Image.new('RGB', (100, 100), color=(i*50, i*50, i*50))
        frames.append(frame)
        durations.append(500)  # 500ms duration for each frame
    
    # Save as animated WebP
    buffer = io.BytesIO()
    frames[0].save(
        buffer, 
        format="WEBP", 
        save_all=True, 
        append_images=frames[1:],
        duration=durations,
        loop=0
    )
    webp_content = buffer.getvalue()
    
    # Save to repository
    card = MCard(content=webp_content)
    await repository.save(card)
    
    # Retrieve and verify
    retrieved = await repository.get(card.hash)
    assert retrieved is not None
    assert retrieved.content == webp_content
    
    # Verify it's still a valid animated WebP
    img = Image.open(io.BytesIO(retrieved.content))
    assert img.format == "WEBP"
    assert getattr(img, "is_animated", False)
    assert img.n_frames > 1
