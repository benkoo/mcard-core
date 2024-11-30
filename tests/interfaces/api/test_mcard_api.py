"""Test MCard API."""
import pytest
import pytest_asyncio
import logging
import asyncio
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.interfaces.api.mcard_api import MCardAPI
from mcard.interfaces.api.async_api_wrapper import AsyncAPIWrapper
from mcard.infrastructure.persistence.async_persistence_wrapper import AsyncPersistenceWrapper as PersistenceWrapper
from mcard.infrastructure.persistence.engine_config import SQLiteConfig
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
    await api.create_card("First card")
    await api.create_card("Second card")
    await api.create_card("Third card")
    await api.create_card("Another one")
    
    # Search for cards containing "card"
    cards = await api.list_cards(content="card")
    assert len(cards) == 3
    
    # Search for cards containing "one"
    cards = await api.list_cards(content="one")
    assert len(cards) == 1

@pytest.mark.asyncio
async def test_list_cards_with_pagination(shared_repo):
    """Test listing cards with pagination."""
    api = shared_repo
    for i in range(10):
        await api.create_card(f"Content {i}")
    
    # Test limit
    cards = await api.list_cards(limit=5)
    assert len(cards) == 5
    
    # Test offset
    cards = await api.list_cards(offset=5, limit=5)
    assert len(cards) == 5

@pytest.mark.asyncio
async def test_remove_card(shared_repo):
    """Test removing a card."""
    api = shared_repo
    content = "Test content"
    card = await api.create_card(content)
    
    # Verify card exists
    assert await api.get_card(card.hash) is not None
    
    # Remove card
    await api.remove_card(card.hash)
    
    # Verify card is removed
    assert await api.get_card(card.hash) is None

@pytest.mark.asyncio
async def test_create_card_large_content(shared_repo):
    """Test creating a card with large content."""
    api = shared_repo
    content = "x" * 1000000  # 1MB of content
    card = await api.create_card(content)
    assert card.content == content

@pytest.mark.asyncio
async def test_create_card_binary_content(shared_repo):
    """Test creating a card with binary content."""
    api = shared_repo
    content = b"Binary content"
    card = await api.create_card(content)
    assert card.content == content
