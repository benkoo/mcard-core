"""Test MCard API."""
import pytest
import pytest_asyncio
import logging
import asyncio
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.interfaces.api.mcard_api import MCardAPI
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.infrastructure.persistence.async_wrapper import AsyncSQLiteWrapper
from mcard.domain.models.exceptions import StorageError

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@pytest_asyncio.fixture(scope="function")
async def shared_repo(async_repository):
    """Create API instance with test database."""
    async with async_repository as repo:
        api = MCardAPI(repository=repo)
        yield api

@pytest.mark.asyncio
async def test_create_card(shared_repo):
    """Test creating a card."""
    api = shared_repo
    content = "Test content"
    card = await api.create_card(content)
    assert card.content == content

@pytest.mark.asyncio
async def test_get_card(shared_repo):
    """Test getting a card."""
    api = shared_repo
    content = "Test content"
    card = await api.create_card(content)
    retrieved = await api.get_card(card.hash)
    assert retrieved.content == content

@pytest.mark.asyncio
async def test_list_cards(shared_repo):
    """Test listing cards."""
    api = shared_repo
    cards = []
    for i in range(5):
        card = await api.create_card(f"Content {i}")
        cards.append(card)
    
    listed = await api.list_cards()
    assert len(listed) == len(cards)

@pytest.mark.asyncio
async def test_list_cards_by_content(shared_repo):
    """Test listing cards by content."""
    api = shared_repo
    cards = []
    for i in range(5):
        card = await api.create_card(f"Content {i}")
        cards.append(card)
    
    # Add a specific card to search for
    search_content = "Unique content"
    search_card = await api.create_card(search_content)
    
    listed = await api.list_cards(content=search_content)
    assert len(listed) == 1
    assert listed[0].hash == search_card.hash

@pytest.mark.asyncio
async def test_list_cards_with_pagination(shared_repo):
    """Test listing cards with pagination."""
    api = shared_repo
    cards = []
    for i in range(10):
        card = await api.create_card(f"Content {i}")
        cards.append(card)
    
    # Test pagination
    page1 = await api.list_cards(limit=5)
    page2 = await api.list_cards(limit=5, offset=5)
    
    assert len(page1) == 5
    assert len(page2) == 5
    assert all(c1.hash != c2.hash for c1 in page1 for c2 in page2)

@pytest.mark.asyncio
async def test_remove_card(shared_repo):
    """Test removing a card."""
    api = shared_repo
    content = "Test content"
    card = await api.create_card(content)
    
    # Remove the card
    await api.remove_card(card.hash)
    
    # Verify it's gone
    with pytest.raises(Exception):
        await api.get_card(card.hash)

@pytest.mark.asyncio
async def test_create_card_large_content(shared_repo):
    """Test creating a card with large content."""
    api = shared_repo
    large_content = "x" * (500 * 1024)
    card = await api.create_card(large_content)
    assert card.content == large_content

@pytest.mark.asyncio
async def test_create_card_binary_content(shared_repo):
    """Test creating a card with binary content."""
    api = shared_repo
    binary_content = bytes([0x00, 0x01, 0x02, 0x03])
    card = await api.create_card(binary_content.hex())
    assert bytes.fromhex(card.content) == binary_content
