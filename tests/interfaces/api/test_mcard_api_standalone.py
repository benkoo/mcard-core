"""Test MCard API standalone mode."""
import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pathlib import Path
from mcard.domain.models.card import MCard
from mcard.interfaces.api.mcard_api import MCardAPI
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig
from mcard.interfaces.api.async_api_wrapper import AsyncAPIWrapper
from mcard.infrastructure.persistence.async_persistence_wrapper import AsyncPersistenceWrapper as PersistenceWrapper

@pytest_asyncio.fixture
async def repository():
    """Create a fresh repository for each test."""
    config = SQLiteConfig(db_path=":memory:")
    persistence = PersistenceWrapper(config)
    wrapper = AsyncAPIWrapper(persistence)
    async with wrapper as repo:
        yield repo

@pytest.mark.asyncio
async def test_mcard_api(repository):
    """Test MCardAPI with in-memory repository."""
    api = MCardAPI(repository=repository)
    
    # Test creating a card
    content = "Test content"
    card = await api.create_card(content)
    assert card.content == content
    
    # Test retrieving the card
    retrieved = await api.get_card(card.hash)
    assert retrieved is not None
    assert retrieved.content == content
    
    # Test listing cards
    cards = await api.list_cards()
    assert len(cards) == 1
    assert cards[0].content == content
    
    # Test deleting the card
    await api.remove_card(card.hash)
    cards = await api.list_cards()
    assert len(cards) == 0
