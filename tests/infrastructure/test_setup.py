"""Tests for MCard setup functionality."""
import os
import pytest
from pathlib import Path

from mcard.infrastructure.setup import MCardSetup
from mcard.infrastructure.persistence.engine_config import EngineType
from mcard.domain.models.exceptions import StorageError


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    return str(tmp_path / "test.db")


@pytest.mark.asyncio
async def test_setup_memory_db():
    """Test setup with in-memory database."""
    setup = MCardSetup()
    await setup.initialize()
    try:
        # Create a test card
        card = await setup.storage.create("Test content")
        assert card.content == "Test content"
        
        # Retrieve the card
        retrieved = await setup.storage.get(card.hash)
        assert retrieved is not None
        assert retrieved.content == "Test content"
    finally:
        await setup.cleanup()


@pytest.mark.asyncio
async def test_setup_file_db(temp_db_path):
    """Test setup with file-based database."""
    setup = MCardSetup(db_path=temp_db_path)
    await setup.initialize()
    try:
        # Create a test card
        card = await setup.storage.create("Test content")
        assert card.content == "Test content"
        
        # Verify file exists
        assert os.path.exists(temp_db_path)
    finally:
        await setup.cleanup()


@pytest.mark.asyncio
async def test_setup_with_config_overrides():
    """Test setup with configuration overrides."""
    overrides = {
        "max_connections": 10,
        "timeout": 10.0,
        "max_content_size": 20 * 1024 * 1024  # 20MB
    }
    setup = MCardSetup(config_overrides=overrides)
    await setup.initialize()
    try:
        # Test increased content size limit
        large_content = "x" * (15 * 1024 * 1024)  # 15MB
        card = await setup.storage.create(large_content)
        assert len(card.content) == len(large_content)
    finally:
        await setup.cleanup()


@pytest.mark.asyncio
async def test_setup_invalid_engine():
    """Test setup with invalid engine type."""
    with pytest.raises(ValueError, match="Unsupported engine type"):
        MCardSetup(engine_type="invalid")


@pytest.mark.asyncio
async def test_setup_context_manager(temp_db_path):
    """Test setup using async context manager."""
    async with MCardSetup(db_path=temp_db_path) as setup:
        card = await setup.storage.create("Test content")
        assert card.content == "Test content"
        
    # Verify cleanup occurred
    assert not hasattr(setup, "_connection")


@pytest.mark.asyncio
async def test_setup_content_interpreter():
    """Test setup content interpreter functionality."""
    setup = MCardSetup()
    await setup.initialize()
    try:
        # Test binary content
        binary_content = b"Binary data"
        assert setup.content_interpreter.is_binary_content(binary_content)
        
        # Test text content
        text_content = "Text data"
        assert not setup.content_interpreter.is_binary_content(text_content)
    finally:
        await setup.cleanup()


@pytest.mark.asyncio
async def test_setup_multiple_instances(temp_db_path):
    """Test multiple setup instances using the same database."""
    setup1 = MCardSetup(db_path=temp_db_path)
    setup2 = MCardSetup(db_path=temp_db_path)
    
    await setup1.initialize()
    await setup2.initialize()
    
    try:
        # Create card with first instance
        card1 = await setup1.storage.create("Content 1")
        
        # Verify with second instance
        card2 = await setup2.storage.get(card1.hash)
        assert card2 is not None
        assert card2.content == "Content 1"
    finally:
        await setup1.cleanup()
        await setup2.cleanup()
