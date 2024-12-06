"""Script to create 1000 MCards with varied content."""
from fastapi.testclient import TestClient
from src.server import app
from mcard.infrastructure.setup import MCardSetup
import os
from pathlib import Path
from datetime import datetime

# Configuration
TEST_API_KEY = "test_api_key"
TEST_DB_PATH = str(Path("./data/mcard.db").absolute())

def create_thousand_cards():
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
    
    # Create 1000 cards
    num_cards = 1000
    created_hashes = []
    
    print(f"\nCreating {num_cards} cards with varied content...")
    for i in range(num_cards):
        # Create varied content to simulate real usage
        content_type = i % 4  # Create 4 different types of content
        
        if content_type == 0:
            # Code snippet
            content = f"""```python
def example_function_{i}():
    print('This is example {i}')
    return {i * i}
```"""
        elif content_type == 1:
            # Markdown text
            content = f"""# Heading {i}
This is a markdown document with some **bold** and *italic* text.
- List item {i}.1
- List item {i}.2
> This is a quote for card {i}"""
        elif content_type == 2:
            # JSON-like content
            content = f"""{{
    "id": {i},
    "name": "Test Object {i}",
    "properties": {{
        "value": {i * 100},
        "timestamp": "{datetime.now().isoformat()}"
    }}
}}"""
        else:
            # Plain text with URLs
            content = f"""Important note {i}
Reference: https://example.com/doc/{i}
See also: https://example.com/related/{i * 2}
Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        response = client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        
        if response.status_code != 200:
            print(f"Error creating card {i}: {response.status_code}")
            continue
            
        card_data = response.json()
        created_hashes.append(card_data["hash"])
        
        if i > 0 and i % 100 == 0:
            print(f"Created {i} cards...")
    
    print("\nVerifying card count...")
    response = client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    
    if response.status_code == 200:
        cards = response.json()
        print(f"Total cards in database: {len(cards)}")
    else:
        print(f"Error getting card count: {response.status_code}")

if __name__ == "__main__":
    print("Starting card creation...")
    create_thousand_cards()
    print("Done!")
