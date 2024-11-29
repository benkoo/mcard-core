"""Test SQLite connection management."""
import logging
import os
import tempfile
import pytest
import sqlite3
from mcard.domain.models.card import MCard
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.infrastructure.persistence.async_wrapper import AsyncSQLiteWrapper
from mcard.domain.models.exceptions import StorageError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture
def repository():
    """Fixture for SQLite repository using in-memory database."""
    repo = SQLiteStore(SQLiteConfig(db_path=":memory:"))
    yield repo

@pytest.fixture
def db_path():
    """Fixture for temporary database path."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def db_repository(db_path):
    """Fixture for SQLite repository using temporary database."""
    repo = SQLiteStore(SQLiteConfig(db_path=db_path))
    yield repo

def test_connection_operations(repository):
    """Test basic connection operations."""
    logging.debug("Starting test_connection_operations")
    
    # Test multiple operations
    for _ in range(10):
        results = repository.get_all()
        assert isinstance(results, list)
    
    # Test connection is still valid by performing a query
    card = MCard(content="Test content")
    repository.save(card)
    retrieved = repository.get(card.hash)
    assert retrieved is not None
    
    logging.debug("Test completed successfully")

def test_error_handling(repository):
    """Test error handling with invalid SQL."""
    logging.debug("Starting test_error_handling")
    
    # Test error handling with invalid SQL using a raw cursor
    conn = repository._get_connection()
    with pytest.raises(sqlite3.OperationalError):
        cursor = conn.cursor()
        cursor.execute("INVALID SQL")
        cursor.close()
    
    # Verify repository is still usable
    card = MCard(content="Test content")
    repository.save(card)
    retrieved = repository.get(card.hash)
    assert retrieved is not None
    
    logging.debug("Test completed successfully")

def test_connection_recovery(db_repository):
    """Test that the repository can recover from connection errors."""
    # First operation should succeed
    card = MCard(content="Test content")
    db_repository.save(card)
    
    # Clear the thread-local storage
    db_repository._local.__dict__.clear()
    
    # Next operation should automatically create a new connection
    retrieved = db_repository.get(card.hash)
    assert retrieved is not None

def test_connection_isolation(db_repository):
    """Test connection isolation."""
    # Create a card
    card = MCard(content="Test content")
    db_repository.save(card)
    
    # Create a new repository instance for the same database
    repo2 = SQLiteStore(SQLiteConfig(db_path=db_repository.db_path))
    
    # Changes should be visible to second connection
    retrieved_card = repo2.get(card.hash)
    assert retrieved_card.content == card.content
    
    # Changes in second connection should be visible to first
    card2 = MCard(content="Test content 2")
    repo2.save(card2)
    retrieved_card2 = db_repository.get(card2.hash)
    assert retrieved_card2.content == card2.content

def test_connection_errors(db_path):
    """Test handling of connection errors."""
    # Test with non-existent directory
    bad_path = "/nonexistent/dir/db.sqlite"
    with pytest.raises(StorageError) as exc_info:
        repo = SQLiteStore(SQLiteConfig(db_path=bad_path))
        repo._get_connection()  # Force connection attempt
    assert "Failed to create or connect to database" in str(exc_info.value)
    
    # Test with read-only directory
    if os.path.exists(db_path):
        os.chmod(db_path, 0o444)  # Make read-only
        with pytest.raises(StorageError) as exc_info:
            repo = SQLiteStore(SQLiteConfig(db_path=db_path))
            repo._get_connection()  # Force connection attempt
        assert "Failed to create or connect to database" in str(exc_info.value)

@pytest.mark.asyncio
async def test_connection_context():
    """Test that the connection context manager works properly."""
    wrapper = AsyncSQLiteWrapper(SQLiteConfig(db_path=":memory:"))
    
    async with wrapper as repo:
        # Verify we can execute a query
        async with repo._get_repository()._get_connection() as conn:
            await conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            await conn.commit()
            
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = await cursor.fetchall()
            assert len(tables) > 0
            assert ("test",) in tables

@pytest.mark.asyncio
async def test_connection_isolation():
    """Test that connections are properly isolated."""
    wrapper1 = AsyncSQLiteWrapper(SQLiteConfig(db_path=":memory:"))
    wrapper2 = AsyncSQLiteWrapper(SQLiteConfig(db_path=":memory:"))
    
    async with wrapper1 as repo1:
        async with wrapper2 as repo2:
            # Create table in first connection
            async with repo1._get_repository()._get_connection() as conn1:
                await conn1.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
                await conn1.commit()
            
            # Verify table doesn't exist in second connection
            async with repo2._get_repository()._get_connection() as conn2:
                cursor = await conn2.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = await cursor.fetchall()
                assert ("test",) not in tables

@pytest.mark.asyncio
async def test_connection_cleanup():
    """Test that connections are properly cleaned up."""
    wrapper = AsyncSQLiteWrapper(SQLiteConfig(db_path=":memory:"))
    
    async with wrapper as repo:
        # Create a table
        async with repo._get_repository()._get_connection() as conn:
            await conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            await conn.commit()
    
    # Verify wrapper is closed
    with pytest.raises(RuntimeError, match="Repository not initialized"):
        wrapper._get_repository()
