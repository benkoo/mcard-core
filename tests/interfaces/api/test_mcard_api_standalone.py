import os
import asyncio
import logging
import pytest
from httpx import AsyncClient
from mcard.interfaces.api.mcard_api import app, load_app_settings, get_repository
from mcard.infrastructure.repository import SQLiteRepository
from mcard.domain.models.config import AppSettings, DatabaseSettings
from mcard.infrastructure.persistence.schema_utils import initialize_schema

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def test_settings():
    """Create test settings."""
    return AppSettings(
        database=DatabaseSettings(
            db_path=":memory:",
            data_source="sqlite",
            pool_size=3,
            timeout=15.0
        ),
        mcard_api_key="test_custom_api_key_12345"
    )

@pytest.fixture
def repository():
    """Create a fresh repository for each test."""
    repo = SQLiteRepository(":memory:")
    initialize_schema(repo.connection)
    return repo

@pytest.fixture
def override_dependencies(test_settings, repository):
    """Override app dependencies for testing."""
    app.dependency_overrides[load_app_settings] = lambda: test_settings
    app.dependency_overrides[get_repository] = lambda: repository
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_mcard_api(override_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"x-api-key": "test_custom_api_key_12345"}
        
        # Test creating a card
        response = await client.post("/cards/", json={"content": "Test content"}, headers=headers)
        assert response.status_code == 201
        card_hash = response.json()["hash"]

        # Test retrieving the card
        response = await client.get(f"/cards/{card_hash}", headers=headers)
        assert response.status_code == 200
        assert response.json()["content"] == "Test content"

        # Test listing cards
        response = await client.get("/cards/", headers=headers)
        assert response.status_code == 200
        cards = response.json()
        assert len(cards) == 1
