import os
import asyncio
import logging
from http import HTTPStatus
from httpx import AsyncClient
from mcard.interfaces.api.mcard_api import app, api
from mcard.infrastructure.persistence.repositories import SQLiteCardRepo
from mcard.infrastructure.persistence.schema import SchemaManager
from mcard.infrastructure.persistence.database_engine_config import EngineType
from mcard.domain.models.card import MCard, CardCreate
from mcard.config_constants import TEST_DB_PATH
from mcard.interfaces.api.api_config_loader import load_config
import pytest
import sqlite3
from datetime import datetime
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
DB_PATH = "./tests/data/test_mcard.db"  # Hardcoded path for testing

# Ensure the database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@pytest.fixture(scope="module")
async def initialized_api():
    """Initialize the API and database."""
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Create the directory if it doesn't exist
    
    # Initialize the store
    store = await api.get_store()
    await store.initialize()  # Make sure schema is initialized
    
    # Initialize the schema
    conn = await aiosqlite.connect(DB_PATH)  # Create a new connection to the database
    schema_manager = SchemaManager()  # Create an instance of SchemaManager
    await schema_manager.initialize_schema(EngineType.SQLITE, conn)
    await conn.close()
    
    try:
        yield api
    finally:
        # Cleanup
        try:
            await api.shutdown()
        except Exception as e:
            logger.error(f"Error during API shutdown: {e}")

@pytest.fixture(autouse=True)
async def cleanup_event_loop():
    """Cleanup the event loop after each test."""
    yield
    try:
        # Get all tasks except current
        current_task = asyncio.current_task()
        tasks = [t for t in asyncio.all_tasks() if t is not current_task]
        
        if tasks:
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            
            # Wait for all tasks to complete with a timeout
            await asyncio.wait(tasks, timeout=5)
            
            # If any tasks are still pending, log them
            pending = [t for t in tasks if not t.done()]
            if pending:
                logger.warning(f"Some tasks did not complete: {len(pending)} tasks remaining")
    except Exception as e:
        logger.error(f"Error during event loop cleanup: {e}")

@pytest.mark.asyncio
async def test_mcard_api_persistent(initialized_api):
    """Test data persistence in the API."""
    # Wait for the fixture to complete
    test_api = await anext(initialized_api.__aiter__())
    
    # Test content
    test_contents = [
        f"Persistent Test Card {i} - {datetime.now().isoformat()}"
        for i in range(1, 4)
    ]
    
    # Create cards directly using the API instance
    created_hashes = []
    db = None
    try:
        # Create a single database connection for all operations
        db = await aiosqlite.connect(DB_PATH)
        
        for content in test_contents:
            # Check if the card already exists in the database
            async with db.execute("SELECT hash FROM card WHERE content = ?", (content,)) as cursor:
                existing_card = await cursor.fetchone()
                if existing_card:
                    logger.debug(f"Card with content '{content}' already exists. Reusing existing card.")
                    created_hashes.append(existing_card[0])  # Use the existing hash
                else:
                    # Create a new card if it doesn't exist
                    card = await test_api.create_card(content)
                    assert card is not None
                    created_hashes.append(card.hash)
                    logger.debug(f"Created new card with hash: {card.hash}")

        # Verify cards were created and can be retrieved
        for hash_str in created_hashes:
            card = await test_api.get_card(hash_str)
            assert card is not None
            logger.debug(f"Retrieved card with hash {hash_str}: {card.content}")

        # List all cards and verify
        all_cards = await test_api.list_cards(page=1, page_size=10)
        assert all_cards is not None
        assert len(all_cards) >= len(test_contents)
        
        # Verify content matches
        card_contents = [card.content for card in all_cards]
        for content in test_contents:
            assert content in card_contents, f"Content '{content}' not found in card contents"

        # Verify database contents
        async with db.execute("SELECT hash, content FROM card") as cursor:
            db_cards = await cursor.fetchall()
            
            logger.debug("\nDatabase Contents:")
            for db_hash, db_content in db_cards:
                logger.debug(f"Hash: {db_hash}, Content: {db_content}")
                if db_content in test_contents:
                    logger.debug(f"Found matching content in database: {db_content}")
            
            # Verify all test contents exist in database
            db_contents = [card[1] for card in db_cards]
            for content in test_contents:
                assert content in db_contents, f"Content '{content}' not found in database"

    finally:
        # Clean up database connection
        if db:
            await db.close()
