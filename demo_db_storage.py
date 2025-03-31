#!/usr/bin/env python
"""
Demo script to demonstrate MCard storage in the SQLite database.
This script creates a card and then verifies it was stored in the database.
"""

import asyncio
import uuid
from datetime import datetime, timezone
import sqlite3
import os
import logging

from mcard.domain.models.card import MCard
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore, SQLiteConfig
from mcard.infrastructure.persistence.database_engine_config import EngineType

# Configure logging
logging.basicConfig(level=logging.DEBUG)

async def demo_card_storage():
    # Create a direct SQLiteStore instance instead of using MCardStore
    # This bypasses the facade layer that's causing the method mismatch
    db_path = os.path.join("data", "DEFAULT_DB_FILE.db")
    print(f"Using database at: {db_path}")
    
    # Create a SQLiteStore instance directly
    config = SQLiteConfig(db_path=db_path)
    store = SQLiteStore(config)
    
    # Initialize the database
    await store.initialize()
    
    # Create a unique test card
    unique_id = uuid.uuid4()
    test_content = f"Test content created at {datetime.now()} with ID {unique_id}"
    test_card = MCard(
        content=test_content,
        hash=None,  # Let the store compute the hash
        g_time=datetime.now(timezone.utc).isoformat()
    )
    
    # Save the card to the database
    print(f"Saving card with content: {test_content}")
    await store.save(test_card)
    print(f"Card saved with hash: {test_card.hash}")
    
    # Retrieve the card using its hash
    retrieved_card = await store.get(test_card.hash)
    print(f"Retrieved card from store API:")
    print(f"  Hash: {retrieved_card.hash}")
    print(f"  Content: {retrieved_card.content}")
    print(f"  Time: {retrieved_card.g_time}")
    
    # Directly query the database to show stored data
    print(f"\nQuerying database directly at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Display the table schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='card'")
    schema = cursor.fetchone()[0]
    print(f"Card table schema: {schema}")
    
    # Query for our specific card
    cursor.execute("SELECT hash, content, g_time FROM card WHERE hash = ?", (test_card.hash,))
    row = cursor.fetchone()
    
    if row:
        print(f"\nCard found in database:")
        print(f"  Hash: {row[0]}")
        print(f"  Content: {row[1]}")
        print(f"  Time: {row[2]}")
    else:
        print("Card not found in direct database query!")
    
    conn.close()
    await store.close()


if __name__ == "__main__":
    asyncio.run(demo_card_storage())
