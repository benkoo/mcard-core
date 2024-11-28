import os
import pytest
import tempfile
import logging
from httpx import AsyncClient
from mcard.interfaces.api.mcard_api import app, load_app_settings, get_repository
from mcard.infrastructure.repository import SQLiteRepository
from mcard.domain.models.config import AppSettings, DatabaseSettings
from mcard.infrastructure.persistence.schema_utils import initialize_schema

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def test_settings(db_path):
    """Create test settings with the temporary database."""
    return AppSettings(
        database=DatabaseSettings(
            db_path=db_path,
            data_source="sqlite",
            pool_size=3,
            timeout=15.0
        ),
        mcard_api_key="test_custom_api_key_12345"
    )

@pytest.fixture
def repository(db_path):
    """Create a repository with the temporary database."""
    repo = SQLiteRepository(db_path)
    initialize_schema(repo.connection)
    return repo

@pytest.mark.asyncio
async def test_mcard_api_persistent(repository, db_path, test_settings):
    # Override app settings for this test
    app.dependency_overrides[load_app_settings] = lambda: test_settings
    app.dependency_overrides[get_repository] = lambda: repository

    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"x-api-key": "test_custom_api_key_12345"}

            # Test creating multiple cards
            card_hashes = []
            for i in range(3):
                response = await client.post("/cards/", json={"content": f"Test content {i}"}, headers=headers)
                assert response.status_code == 201
                card_hash = response.json()["hash"]
                card_hashes.append(card_hash)

            # Test retrieving all cards
            response = await client.get("/cards/", headers=headers)
            assert response.status_code == 200
            cards = response.json()
            assert len(cards) == 3

            # Test retrieving individual cards
            for card_hash in card_hashes:
                response = await client.get(f"/cards/{card_hash}", headers=headers)
                assert response.status_code == 200
                card = response.json()
                assert card["hash"] == card_hash

            # Test deleting cards
            for card_hash in card_hashes:
                response = await client.delete(f"/cards/{card_hash}", headers=headers)
                assert response.status_code == 204
    finally:
        # Clear overrides
        app.dependency_overrides.clear()
