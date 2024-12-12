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
import pytest
import sqlite3
from datetime import datetime
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Specify the database file path
DB_PATH = './data/ROOT_mcard_DOT_ENV.db'  # Use the same database path as the API

# Ensure the database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@pytest.fixture(scope="module")
@pytest.mark.asyncio
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
    
    # Clean up any existing data using direct SQLite connection
    try:
        cursor = await conn.cursor()
        await cursor.execute('DELETE FROM card')
        await conn.commit()
    finally:
        await conn.close()  # Close the connection properly
    
    # Also clean through API for good measure
    await api.delete_all_cards()
    
    # Verify database is empty
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM card')
        count = cursor.fetchone()[0]
        assert count == 0, f"Database not empty after cleanup, found {count} records"
    finally:
        conn.close()
    
    # Return the API instance
    return api

@pytest.mark.asyncio
async def test_mcard_api_persistent(initialized_api):
    """Test data persistence in the API."""
    # Wait for the fixture to complete
    test_api = await initialized_api
    
    # Test content
    test_contents = [
        f"Persistent Test Card {i} - {datetime.now().isoformat()}"
        for i in range(1, 4)
    ]
    
    # Create cards directly using the API instance
    created_hashes = []
    for content in test_contents:
        logger.debug(f"Attempting to create card with content: {content}")
        card = await test_api.create_card(content)
        assert card is not None
        created_hashes.append(card.hash)
        logger.debug(f"Created card with hash: {card.hash}")

    # Verify cards were created and can be retrieved
    for hash_str in created_hashes:
        card = await test_api.get_card(hash_str)
        assert card is not None
        assert card.hash in created_hashes
        logger.debug(f"Retrieved card with hash: {card.hash}")

    # List all cards and verify
    all_cards = await test_api.list_cards(page=1, page_size=10)
    assert all_cards is not None
    assert len(all_cards) == len(test_contents)
    
    # Verify content matches
    card_contents = [card.content for card in all_cards]
    for content in test_contents:
        assert content in card_contents

    # Directly verify database contents
    async def verify_database_contents():
        logger.debug(f"Verifying database contents in {DB_PATH}")
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT hash, content FROM card") as cursor:
                db_cards = await cursor.fetchall()
                
                logger.debug("\nDatabase Contents:")
                for db_hash, db_content in db_cards:
                    logger.debug(f"Hash: {db_hash}, Content: {db_content}")
                    assert db_content in test_contents, f"Content {db_content} not found in expected contents"
                
                # Verify the number of cards
                assert len(db_cards) == len(test_contents), f"Expected {len(test_contents)} cards but found {len(db_cards)} in database"
    
    # Wait for verification to complete
    await verify_database_contents()

    # Cleanup after all tests are done
    await test_api.delete_all_cards()
    store = await test_api.get_store()
    await store.close()
    await test_api.shutdown()
