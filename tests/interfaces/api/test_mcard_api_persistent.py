"""Test MCard API persistent storage."""
import os
import pytest
import pytest_asyncio
import tempfile
from fastapi.testclient import TestClient
from pathlib import Path
from mcard.domain.models.card import MCard
from mcard.interfaces.api.mcard_api import MCardAPI
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig
from mcard.interfaces.api.async_api_wrapper import AsyncAPIWrapper
from mcard.infrastructure.persistence.async_persistence_wrapper import AsyncPersistenceWrapper as PersistenceWrapper

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    temp_path = tempfile.mktemp()
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest_asyncio.fixture
async def async_repository(db_path):
    """Create a repository with the temporary database."""
    persistence = PersistenceWrapper(SQLiteConfig(db_path=db_path))
    wrapper = AsyncAPIWrapper(persistence)
    async with wrapper as repo:
        yield repo

@pytest.mark.asyncio
async def test_mcard_api_persistent(async_repository):
    """Test MCard API with persistent storage."""
    # Initialize API with repository
    api = MCardAPI(repository=async_repository)
    assert api.repository is not None  # Verify repository is properly set

    # Test creating a card
    content = "Test content"
    card = await api.create_card(content)
    assert card.content == content

    # Test getting a card
    retrieved = await api.get_card(card.hash)
    assert retrieved.content == content

    # Test listing cards
    cards = await api.list_cards()
    assert len(cards) == 1
    assert cards[0].content == content

    # Test removing a card
    await api.remove_card(card.hash)
    cards = await api.list_cards()
    assert len(cards) == 0
