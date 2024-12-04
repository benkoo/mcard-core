import os
import asyncio
import logging
from httpx import AsyncClient
from mcard.interfaces.api.mcard_api import app
from mcard.infrastructure.persistence.sqlite import SQLiteRepository

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create an in-memory repository
shared_repo = SQLiteStore(db_path=':memory:')

async def test_mcard_api():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test creating a card
        print("Testing card creation...")
        create_response = await client.post("/cards/", 
                                            json={"content": "Test content"}, 
                                            headers={"x-api-key": "test_api_key"})
        print("Create Response:", create_response.json())
        assert create_response.status_code == 200
        
        # Get the created card's hash
        card_hash = create_response.json().get("hash")
        
        # Test retrieving the card
        print("Testing card retrieval...")
        get_response = await client.get(f"/cards/{card_hash}", 
                                        headers={"x-api-key": "test_api_key"})
        print("Get Response:", get_response.json())
        assert get_response.status_code == 200
        
        # Test listing cards
        print("Testing card listing...")
        list_response = await client.get("/cards/", 
                                         headers={"x-api-key": "test_api_key"})
        print("List Response:", list_response.json())
        assert list_response.status_code == 200

if __name__ == "__main__":
    asyncio.run(test_mcard_api())
