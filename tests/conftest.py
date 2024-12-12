import asyncio
import os
import sys
import pytest
import pytest_asyncio
from pathlib import Path

from mcard.infrastructure.infrastructure_config_manager import get_project_root
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig
from mcard.infrastructure.persistence.store import SQLiteStore
from mcard.domain.services.hashing import DefaultHashingService, HashingSettings

# Configure asyncio for pytest
def pytest_configure(config):
    """Configure pytest with async support."""
    config.addinivalue_line(
        "markers", "async_test: mark a test as an async test"
    )
    
    # Set asyncio policy to use ProactorEventLoop on Windows, SelectorEventLoop on Unix
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

def pytest_collection_modifyitems(config, items):
    """Modify test items to support async tests."""
    for item in items:
        if hasattr(item, "obj") and asyncio.iscoroutinefunction(item.obj):
            item.add_marker(pytest.mark.asyncio)

@pytest.fixture(scope="session")
def event_loop(request):
    """Create an event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    policy.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def default_service():
    """Create a default hashing service for testing."""
    settings = HashingSettings(algorithm="sha256")
    service = DefaultHashingService(settings)
    return service

@pytest_asyncio.fixture(scope="function")
async def async_repository():
    """Create a repository with a temporary in-memory database."""
    config = SQLiteConfig(db_path=":memory:")
    repo = SQLiteStore(config)
    await repo.initialize()
    yield repo
    await repo.close()

@pytest_asyncio.fixture(scope="function")
async def repository(async_repository):
    """Yield the async repository for tests."""
    yield async_repository

@pytest_asyncio.fixture(scope="function")
async def db_path():
    """Generate a temporary database path for testing."""
    test_data_dir = get_project_root() / "tests" / "data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    db_path = test_data_dir / f"test_mcard_{os.getpid()}.db"
    yield str(db_path)
    # Clean up the database file after the test
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass

# Add a custom marker for async tests
def pytest_configure(config):
    """Add custom markers for pytest."""
    config.addinivalue_line(
        "markers", "async_test: mark a test as an async test"
    )

# Monkey patch to handle coroutines in tests
def pytest_pyfunc_call(pyfuncitem):
    """Monkey patch to handle coroutine functions in pytest."""
    if asyncio.iscoroutinefunction(pyfuncitem.obj):
        # Get the event loop
        event_loop = asyncio.get_event_loop()
        
        # Run the coroutine
        try:
            result = event_loop.run_until_complete(pyfuncitem.obj(*pyfuncitem.funcargs.values()))
            return True
        except Exception as e:
            # Re-raise the exception
            raise e
    
    return False
