"""Tests for the FastAPI server."""
import pytest
from httpx import AsyncClient, ASGITransport
import os
from pathlib import Path
from datetime import datetime
from mcard.infrastructure.setup import MCardSetup
from src.server import app
import random

# Test configuration
TEST_API_KEY = "test_api_key"
TEST_DB_PATH = "./data/test_mcard.db"

@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    # Store original environment variables
    original_env = {
        "MCARD_API_KEY": os.environ.get("MCARD_API_KEY"),
        "MCARD_STORE_PATH": os.environ.get("MCARD_STORE_PATH"),
    }
    
    # Set test environment variables
    os.environ["MCARD_API_KEY"] = TEST_API_KEY
    os.environ["MCARD_STORE_PATH"] = TEST_DB_PATH
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

@pytest.fixture(autouse=True)
async def setup_test_db(request):
    """Setup test database."""
    # Skip cleanup if we're running the thousand cards test
    skip_cleanup = request.node.name == "test_create_thousand_cards"
    
    # Ensure test data directory exists
    Path("./data").mkdir(exist_ok=True)
    
    # Remove test database if it exists
    try:
        Path(TEST_DB_PATH).unlink(missing_ok=True)
    except Exception:
        pass
        
    # Create a new setup instance with test database
    setup = MCardSetup(
        db_path=TEST_DB_PATH,
        max_connections=5,
        timeout=5.0
    )
    
    # Initialize database
    await setup.initialize()
    
    # Update app's setup instance
    app.state.setup = setup
    
    yield
    
    # Cleanup only if not the thousand cards test
    if not skip_cleanup:
        await setup.cleanup()
        try:
            Path(TEST_DB_PATH).unlink(missing_ok=True)
        except Exception:
            pass

@pytest.fixture
async def async_client():
    """Create async client for testing."""
    # Reset the API key in the app
    app.state.api_key = TEST_API_KEY
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test health check endpoint."""
    response = await async_client.get(
        "/health",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_invalid_api_key(async_client):
    """Test invalid API key."""
    response = await async_client.get(
        "/health",
        headers={"X-API-Key": "invalid_key"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"

@pytest.mark.asyncio
async def test_create_card(async_client):
    """Test creating a card."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": "Test content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test content"
    assert "hash" in data
    assert "g_time" in data

@pytest.mark.asyncio
async def test_get_card(async_client):
    """Test getting a card."""
    # First create a card
    create_response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": "Test content"}
    )
    assert create_response.status_code == 200
    card_hash = create_response.json()["hash"]
    
    # Then get the card
    get_response = await async_client.get(
        f"/cards/{card_hash}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["content"] == "Test content"
    assert data["hash"] == card_hash

@pytest.mark.asyncio
async def test_list_cards(async_client):
    """Test listing cards."""
    # Create a few cards
    contents = ["Test 1", "Test 2", "Test 3"]
    for content in contents:
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
    
    # List all cards
    response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    cards = response.json()
    assert len(cards) == len(contents)
    assert all(card["content"] in contents for card in cards)

@pytest.mark.asyncio
async def test_delete_card(async_client):
    """Test deleting a card."""
    # First create a card
    create_response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": "Test content"}
    )
    assert create_response.status_code == 200
    card_hash = create_response.json()["hash"]
    
    # Delete the card
    delete_response = await async_client.delete(
        f"/cards/{card_hash}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert delete_response.status_code == 200
    
    # Verify card is deleted
    get_response = await async_client.get(
        f"/cards/{card_hash}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Card not found"

@pytest.mark.asyncio
async def test_create_card_empty_content(async_client):
    """Test creating a card with empty content."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": ""}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Content cannot be empty"

@pytest.mark.asyncio
async def test_create_card_missing_content(async_client):
    """Test creating a card with missing content field."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={}
    )
    assert response.status_code == 422  # FastAPI validation error

@pytest.mark.asyncio
async def test_delete_nonexistent_card(async_client):
    """Test deleting a non-existent card."""
    response = await async_client.delete(
        "/cards/nonexistent_hash",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Card not found"

@pytest.mark.asyncio
async def test_get_cards_empty_db(async_client):
    """Test listing cards with empty database."""
    response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_bulk_card_operations(async_client):
    """Test creating, listing, and deleting hundreds of cards."""
    # Create 500 cards with unique content
    num_cards = 500
    created_hashes = []
    
    print(f"\nCreating {num_cards} cards...")
    for i in range(num_cards):
        content = f"Test content {i} - {datetime.now().isoformat()}"
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        card_data = response.json()
        assert card_data["content"] == content
        created_hashes.append(card_data["hash"])
    
    # List all cards and verify count
    print("Listing all cards...")
    list_response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert list_response.status_code == 200
    cards = list_response.json()
    assert len(cards) >= num_cards  # Greater than or equal because there might be other cards
    
    # Verify each created card can be retrieved
    print("Verifying each card...")
    for card_hash in created_hashes:
        get_response = await async_client.get(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert get_response.status_code == 200
        card_data = get_response.json()
        assert card_data["hash"] == card_hash
    
    # Delete all created cards
    print("Deleting all cards...")
    for card_hash in created_hashes:
        delete_response = await async_client.delete(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert delete_response.status_code == 200
    
    # Verify all cards are deleted
    print("Verifying deletion...")
    for card_hash in created_hashes:
        get_response = await async_client.get(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert get_response.status_code == 404
    
    # Final list check
    final_list_response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert final_list_response.status_code == 200
    remaining_cards = final_list_response.json()
    # Check that all our created cards are gone
    remaining_hashes = {card["hash"] for card in remaining_cards}
    assert not any(h in remaining_hashes for h in created_hashes)

@pytest.mark.asyncio
async def test_concurrent_card_operations(async_client):
    """Test concurrent creation and deletion of cards."""
    import asyncio
    
    # Create 100 cards concurrently
    num_cards = 100
    print(f"\nConcurrently creating {num_cards} cards...")
    
    async def create_card(i):
        content = f"Concurrent test content {i} - {datetime.now().isoformat()}"
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        return response.json()["hash"]
    
    # Create cards concurrently
    creation_tasks = [create_card(i) for i in range(num_cards)]
    created_hashes = await asyncio.gather(*creation_tasks)
    
    # List all cards and verify count
    list_response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert list_response.status_code == 200
    cards = list_response.json()
    assert len(cards) >= num_cards
    
    # Concurrently delete all created cards
    print("Concurrently deleting all cards...")
    
    async def delete_card(card_hash):
        response = await async_client.delete(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200
        return card_hash
    
    # Delete cards concurrently
    deletion_tasks = [delete_card(h) for h in created_hashes]
    deleted_hashes = await asyncio.gather(*deletion_tasks)
    assert set(deleted_hashes) == set(created_hashes)
    
    # Verify all cards are deleted
    print("Verifying concurrent deletion...")
    for card_hash in created_hashes:
        get_response = await async_client.get(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_create_thousand_cards(async_client):
    """Create 1000 MCards with varied content and leave them in the database."""
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

        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        card_data = response.json()
        assert card_data["content"] == content
        created_hashes.append(card_data["hash"])
        
        if i > 0 and i % 100 == 0:
            print(f"Created {i} cards...")
    
    print("All cards created successfully!")
    
    # Verify we can list all cards
    list_response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert list_response.status_code == 200
    cards = list_response.json()
    assert len(cards) >= num_cards
    
    # Verify we can retrieve each card
    print("\nVerifying random sample of created cards...")
    # Check 10 random cards to verify they're accessible
    for card_hash in random.sample(created_hashes, 10):
        get_response = await async_client.get(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert get_response.status_code == 200
        card_data = get_response.json()
        assert card_data["hash"] == card_hash
    
    print(f"\nSuccessfully created and verified {num_cards} cards!")
    print("Cards have been left in the database for further testing.")
    
    # Return the hashes in case they're needed for future tests
    return created_hashes
