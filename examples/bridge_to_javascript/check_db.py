"""Script to check MCard database content."""
import pytest
from httpx import AsyncClient
import asyncio
from src.server import app
import os
from fastapi.testclient import TestClient
from mcard.infrastructure.setup import MCardSetup
from pathlib import Path

# Configuration
TEST_API_KEY = "test_api_key"
TEST_DB_PATH = str(Path("./data/mcard.db").absolute())  # Use absolute path

def check_database():
    # Set environment variables
    os.environ["MCARD_API_KEY"] = TEST_API_KEY
    os.environ["MCARD_STORE_PATH"] = TEST_DB_PATH
    
    # Initialize database
    print(f"Connecting to database at: {TEST_DB_PATH}")
    setup = MCardSetup(
        db_path=TEST_DB_PATH,
        max_connections=5,
        timeout=5.0
    )
    app.state.setup = setup
    
    # Create test client
    client = TestClient(app)
    
    # Get all cards
    response = client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    if response.status_code != 200:
        print(f"Error accessing database: {response.status_code}")
        if response.status_code == 500:
            print(f"Response text: {response.text}")
        return
    
    cards = response.json()
    
    # Print statistics
    print(f"\nTotal number of MCards in database: {len(cards)}")
    
    # Print sample of different content types
    code_cards = [card for card in cards if "```python" in card["content"]]
    markdown_cards = [card for card in cards if "# Heading" in card["content"]]
    json_cards = [card for card in cards if '"properties":' in card["content"]]
    text_cards = [card for card in cards if "Reference: https://" in card["content"]]
    
    print(f"\nBreakdown by type:")
    print(f"Python code snippets: {len(code_cards)}")
    print(f"Markdown documents: {len(markdown_cards)}")
    print(f"JSON content: {len(json_cards)}")
    print(f"Text with URLs: {len(text_cards)}")
    
    # Print a sample from each type
    def print_sample(cards, type_name):
        if cards:
            print(f"\nSample {type_name}:")
            print("-" * 40)
            content = cards[0]["content"]
            print(content[:200] + "..." if len(content) > 200 else content)
            print("-" * 40)
    
    print_sample(code_cards, "Python code")
    print_sample(markdown_cards, "Markdown document")
    print_sample(json_cards, "JSON content")
    print_sample(text_cards, "Text with URL")

if __name__ == "__main__":
    print("Checking database content...")
    check_database()
