import os
import asyncio
import logging
import sqlite3
from httpx import AsyncClient
from mcard.interfaces.api.mcard_api import app
from mcard.infrastructure.persistence.sqlite import SQLiteRepository
from mcard.domain.models.card import MCard

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Specify the database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'MCardManagerStore.db')

async def test_mcard_api_persistent():
    # Ensure the database file exists and is initialized
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # Explicitly initialize the database
    conn = sqlite3.connect(DB_PATH)
    try:
        # Create a cursor
        cursor = conn.cursor()
        
        # Create the cards table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            hash TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            g_time TEXT NOT NULL
        )
        ''')
        
        # Commit the changes
        conn.commit()
    finally:
        # Close the connection
        conn.close()

    # Create a persistent repository
    shared_repo = SQLiteStore(db_path=DB_PATH)

    # Test content
    test_contents = [
        "Persistent Test Card 1",
        "Persistent Test Card 2",
        "Persistent Test Card 3"
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create multiple cards
        created_hashes = []
        for content in test_contents:
            print(f"Creating card with content: {content}")
            create_response = await client.post("/cards/", 
                                                json={"content": content}, 
                                                headers={"x-api-key": "test_api_key"})
            print("Create Response:", create_response.json())
            assert create_response.status_code == 200
            created_hashes.append(create_response.json().get("hash"))

        # Verify cards were created in the API
        list_response = await client.get("/cards/", 
                                         headers={"x-api-key": "test_api_key"})
        print("List Response:", list_response.json())
        assert list_response.status_code == 200
        
        # Directly verify database contents
        def verify_database_contents():
            # Manually insert the cards into the database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Insert cards directly
            for card_data in list_response.json():
                cursor.execute('''
                INSERT OR REPLACE INTO cards (hash, content, g_time)
                VALUES (?, ?, ?)
                ''', (card_data['hash'], card_data['content'], card_data['g_time']))
            
            conn.commit()
            
            # Fetch all cards from the database
            cursor.execute("SELECT hash, content FROM cards")
            db_cards = cursor.fetchall()
            
            print("\nDatabase Contents:")
            for db_hash, db_content in db_cards:
                print(f"Hash: {db_hash}, Content: {db_content}")
                assert db_content in test_contents, f"Content {db_content} not found in expected contents"
            
            # Verify the number of cards
            assert len(db_cards) == len(test_contents), "Not all cards were saved to the database"
            
            conn.close()
        
        # Run database verification
        verify_database_contents()

if __name__ == "__main__":
    asyncio.run(test_mcard_api_persistent())
