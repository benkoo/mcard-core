import pytest
import os
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import mcard_storage_service
from mcard_storage_service import get_repository
from mcard.domain.models.config import AppSettings
from mcard.infrastructure.persistence.schema_initializer import _shared_repository_instance

async def reset_repository():
    """Reset the shared repository instance."""
    global _shared_repository_instance
    if _shared_repository_instance is not None:
        await _shared_repository_instance.close()
    _shared_repository_instance = None

@pytest.fixture
def test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv('TESTING', 'true')
    monkeypatch.setenv('MCARD_MANAGER_DATA_SOURCE', 'sqlite')
    monkeypatch.setenv('MCARD_API_KEY', 'test_api_key_12345')

@pytest.mark.asyncio
async def test_database_file_creation(test_env):
    """Test that the database file is created at the specified path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        os.environ['MCARD_MANAGER_DB_PATH'] = db_path
        
        # Reset the shared repository instance
        await reset_repository()
        
        client = TestClient(mcard_storage_service.app)
        
        # Create a card to initialize the database
        response = client.post(
            "/cards/",
            headers={"X-API-Key": "test_api_key_12345"},
            json={"content": "Test card"}
        )
        assert response.status_code == 201
        
        # Verify database file exists
        assert os.path.exists(db_path)

@pytest.mark.asyncio
async def test_database_persistence(test_env):
    """Test that data persists between service restarts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chmod(temp_dir, 0o777)  # Ensure directory is writable
        db_path = os.path.join(temp_dir, "test_persistence.db")
        os.environ['MCARD_MANAGER_DB_PATH'] = db_path
        
        # Reset the shared repository instance
        await reset_repository()
        
        # First client session - create data
        client1 = TestClient(mcard_storage_service.app)
        response = client1.post(
            "/cards/",
            headers={"X-API-Key": "test_api_key_12345"},
            json={"content": "Persistent card"}
        )
        assert response.status_code == 201
        card_hash = response.json()['hash']
        
        # Second client session - verify data persists
        client2 = TestClient(mcard_storage_service.app)
        response = client2.get(
            f"/cards/{card_hash}",
            headers={"X-API-Key": "test_api_key_12345"}
        )
        assert response.status_code == 200
        assert response.json()['content'] == "Persistent card"

@pytest.mark.asyncio
async def test_database_file_permissions(test_env):
    """Test that the database file has correct permissions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chmod(temp_dir, 0o777)  # Ensure directory is writable
        db_path = os.path.join(temp_dir, "test_permissions.db")
        os.environ['MCARD_MANAGER_DB_PATH'] = db_path
        
        # Reset the shared repository instance
        await reset_repository()
        
        client = TestClient(mcard_storage_service.app)
        
        # Create a card to initialize the database
        response = client.post(
            "/cards/",
            headers={"X-API-Key": "test_api_key_12345"},
            json={"content": "Test card"}
        )
        assert response.status_code == 201
        
        # Verify database file exists and has correct permissions
        assert os.path.exists(db_path)
        st = os.stat(db_path)
        assert bool(st.st_mode & 0o400)  # User can read
        assert bool(st.st_mode & 0o200)  # User can write

@pytest.mark.asyncio
async def test_database_connection_pool(test_env):
    """Test that the database connection pool is configured correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chmod(temp_dir, 0o777)  # Ensure directory is writable
        db_path = os.path.join(temp_dir, "test_pool.db")
        pool_size = 5
        
        os.environ['MCARD_MANAGER_DB_PATH'] = db_path
        os.environ['MCARD_MANAGER_POOL_SIZE'] = str(pool_size)
        
        # Reset the shared repository instance
        await reset_repository()
        
        client = TestClient(mcard_storage_service.app)
        
        # Make multiple concurrent requests to test pool
        responses = []
        for _ in range(pool_size):  # Test with exactly pool size number of requests
            response = client.post(
                "/cards/",
                headers={"X-API-Key": "test_api_key_12345"},
                json={"content": "Pool test card"}
            )
            responses.append(response)
        
        # Verify all requests were successful
        assert all(r.status_code == 201 for r in responses)
        
        # Verify database file exists
        assert os.path.exists(db_path)

@pytest.mark.asyncio
async def test_invalid_database_path(test_env):
    """Test handling of invalid database paths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use a non-existent subdirectory
        invalid_dir = os.path.join(temp_dir, "nonexistent")
        db_path = os.path.join(invalid_dir, "test.db")
        
        os.environ['MCARD_MANAGER_DB_PATH'] = db_path
        
        # Reset the shared repository instance
        await reset_repository()
        
        client = TestClient(mcard_storage_service.app)
        
        # Attempt to create a card
        response = client.post(
            "/cards/",
            headers={"X-API-Key": "test_api_key_12345"},
            json={"content": "Test card"}
        )
        
        # Should succeed since we now create parent directories
        assert response.status_code == 201
        assert os.path.exists(db_path)
