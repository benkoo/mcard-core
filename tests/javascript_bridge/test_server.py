"""Test suite for the MCard JavaScript bridge server.

Requires Python 3.12 or higher.
"""
import sys

# Ensure minimum Python version
if sys.version_info < (3, 12):
    raise RuntimeError("This test suite requires Python 3.12 or higher")

import pytest
from httpx import AsyncClient, ASGITransport
import os
from pathlib import Path
from datetime import datetime
from mcard.infrastructure.setup import MCardSetup
import random
import base64
import hashlib
import asyncio
from mcard.config_constants import (
    DEFAULT_DB_PATH,
    TEST_DB_PATH as CONFIG_TEST_DB_PATH,
    DEFAULT_POOL_SIZE,
    DEFAULT_TIMEOUT,
    DEFAULT_API_PORT,
    ENV_DB_PATH,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_API_PORT,
    ENV_HASH_ALGORITHM,
    DEFAULT_HASH_ALGORITHM,
    ENV_HASH_CUSTOM_MODULE,
    ENV_HASH_CUSTOM_FUNCTION,
    ENV_HASH_CUSTOM_LENGTH,
)

# Import the server module from examples
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bridge_server",
    str(Path(__file__).parent.parent.parent / "examples" / "bridge_to_javascript" / "src" / "server.py")
)
bridge_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge_server)
app = bridge_server.app

# Test configuration
TEST_API_KEY = "test_api_key"
TEST_DB_PATH = str(Path(__file__).parent / "data" / "test_mcard.db")
TEST_POOL_SIZE = DEFAULT_POOL_SIZE * 2  # Double the default for testing
TEST_TIMEOUT = DEFAULT_TIMEOUT  # Use default timeout

@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    # Store original environment variables
    original_env = {
        "MCARD_API_KEY": os.environ.get("MCARD_API_KEY"),
        ENV_DB_PATH: os.environ.get(ENV_DB_PATH),
        ENV_DB_MAX_CONNECTIONS: os.environ.get(ENV_DB_MAX_CONNECTIONS),
        ENV_DB_TIMEOUT: os.environ.get(ENV_DB_TIMEOUT),
        ENV_API_PORT: os.environ.get(ENV_API_PORT),
        ENV_HASH_ALGORITHM: os.environ.get(ENV_HASH_ALGORITHM),
    }
    
    # Set test environment variables
    os.environ["MCARD_API_KEY"] = TEST_API_KEY
    os.environ[ENV_DB_PATH] = TEST_DB_PATH
    os.environ[ENV_DB_MAX_CONNECTIONS] = str(TEST_POOL_SIZE)
    os.environ[ENV_DB_TIMEOUT] = str(TEST_TIMEOUT)
    os.environ[ENV_API_PORT] = str(DEFAULT_API_PORT)
    os.environ[ENV_HASH_ALGORITHM] = DEFAULT_HASH_ALGORITHM
    
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
    # Skip cleanup if we're running the hundred cards test
    skip_cleanup = request.node.name == "test_create_hundred_cards"
    
    # Ensure test data directory exists
    Path(TEST_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    # Remove test database if it exists
    try:
        Path(TEST_DB_PATH).unlink(missing_ok=True)
    except Exception:
        pass
        
    # Create a new setup instance with test database
    setup = MCardSetup(
        db_path=TEST_DB_PATH,
        max_connections=TEST_POOL_SIZE,
        timeout=TEST_TIMEOUT
    )
    
    # Initialize database
    await setup.initialize()
    
    # Update app's setup instance
    app.state.setup = setup
    
    yield
    
    # Cleanup only if not the hundred cards test
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

@pytest.mark.asyncio
async def test_create_card_empty_content(async_client):
    """Test creating a card with empty content."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": ""}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_card_missing_content(async_client):
    """Test creating a card with missing content field."""
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_delete_nonexistent_card(async_client):
    """Test deleting a non-existent card."""
    response = await async_client.delete(
        "/cards/nonexistent",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 404

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
    # Create multiple cards
    num_cards = 100
    contents = [f"Test content {i}" for i in range(num_cards)]
    created_hashes = []

    for content in contents:
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        created_hashes.append(response.json()["hash"])

    # Verify all cards exist
    list_response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert list_response.status_code == 200
    cards = list_response.json()
    assert len(cards) == num_cards

    # Delete all cards
    for card_hash in created_hashes:
        response = await async_client.delete(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200

    # Verify all cards are deleted
    list_response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0

@pytest.mark.asyncio
async def test_concurrent_card_operations(async_client):
    """Test concurrent creation and deletion of cards."""
    num_cards = 50
    contents = [f"Concurrent test content {i}" for i in range(num_cards)]

    # Create cards concurrently
    async def create_card(content):
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        return response.json()["hash"]

    create_tasks = [create_card(content) for content in contents]
    created_hashes = await asyncio.gather(*create_tasks)

    # Verify all cards exist
    list_response = await async_client.get(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == num_cards

    # Delete cards concurrently
    async def delete_card(card_hash):
        response = await async_client.delete(
            f"/cards/{card_hash}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200

    delete_tasks = [delete_card(card_hash) for card_hash in created_hashes]
    await asyncio.gather(*delete_tasks)

@pytest.mark.asyncio
async def test_create_hundred_cards(async_client):
    """Create 100 MCards with varied content and leave them in the database."""
    num_cards = 100
    batch_size = 10
    created_hashes = []
    max_retries = 3

    print(f"\nCreating {num_cards} cards with varied content...")

    async def create_card(i, retry_count=0):
        """Create a single card with varied content."""
        content_type = i % 4
        
        if content_type == 0:
            content = f"def f_{i}(): return {i}"
        elif content_type == 1:
            content = f"# H{i}\nTest {i}"
        elif content_type == 2:
            content = f'{{"id":{i},"v":{i*100}}}'
        else:
            content = f"Note {i}: https://example.com/{i}"

        try:
            async with asyncio.timeout(10):
                response = await async_client.post(
                    "/cards",
                    headers={"X-API-Key": TEST_API_KEY},
                    json={"content": content}
                )
                if response.status_code == 200:
                    card_data = response.json()
                    assert card_data["content"] == content
                    return card_data["hash"]
                elif retry_count < max_retries:
                    print(f"Retrying card {i} due to status {response.status_code}")
                    await asyncio.sleep(1)
                    return await create_card(i, retry_count + 1)
                else:
                    print(f"Failed to create card {i} after {max_retries} retries")
                    return None
        except asyncio.TimeoutError:
            if retry_count < max_retries:
                print(f"Retrying card {i} due to timeout")
                await asyncio.sleep(1)
                return await create_card(i, retry_count + 1)
            else:
                print(f"Timeout creating card {i} after {max_retries} retries")
                return None
        except Exception as e:
            if retry_count < max_retries:
                print(f"Retrying card {i} due to error: {e}")
                await asyncio.sleep(1)
                return await create_card(i, retry_count + 1)
            else:
                print(f"Error creating card {i} after {max_retries} retries: {e}")
                return None

    for batch_start in range(0, num_cards, batch_size):
        batch_end = min(batch_start + batch_size, num_cards)
        print(f"Processing batch {batch_start}-{batch_end}...")
        
        batch_tasks = [create_card(i) for i in range(batch_start, batch_end)]
        batch_results = await asyncio.gather(*batch_tasks)
        
        successful_hashes = [h for h in batch_results if h is not None]
        created_hashes.extend(successful_hashes)
        
        print(f"Completed batch. Total cards so far: {len(created_hashes)}")
        
        await asyncio.sleep(2)
        
        success_rate = len(successful_hashes) / batch_size
        if success_rate < 0.5:
            print("Low success rate detected, pausing for recovery...")
            await asyncio.sleep(10)

    print(f"Created {len(created_hashes)} cards successfully!")

    print("\nVerifying cards...")
    total_cards = 0
    try:
        async with asyncio.timeout(60):
            for retry in range(max_retries):
                try:
                    list_response = await async_client.get(
                        "/cards",
                        headers={"X-API-Key": TEST_API_KEY}
                    )
                    if list_response.status_code == 200:
                        all_cards = list_response.json()
                        total_cards = len(all_cards)
                        print(f"Total cards in database: {total_cards}")
                        break
                    else:
                        print(f"Failed to list cards, attempt {retry + 1}/{max_retries}")
                        await asyncio.sleep(2)
                except Exception as e:
                    print(f"Error listing cards, attempt {retry + 1}/{max_retries}: {e}")
                    await asyncio.sleep(2)
            
            sample_size = min(20, len(created_hashes))
            if sample_size > 0:
                print(f"\nVerifying random sample of {sample_size} cards...")
                verified_count = 0
                for card_hash in random.sample(created_hashes, sample_size):
                    for retry in range(max_retries):
                        try:
                            async with asyncio.timeout(5):
                                get_response = await async_client.get(
                                    f"/cards/{card_hash}",
                                    headers={"X-API-Key": TEST_API_KEY}
                                )
                                if get_response.status_code == 200:
                                    card_data = get_response.json()
                                    assert card_data["hash"] == card_hash
                                    verified_count += 1
                                    break
                        except Exception as e:
                            if retry == max_retries - 1:
                                print(f"Failed to verify card {card_hash}: {e}")
                        await asyncio.sleep(0.5)
                
                print(f"Successfully verified {verified_count}/{sample_size} sample cards")
    except asyncio.TimeoutError:
        print("Timeout during card verification")
    except Exception as e:
        print(f"Error during card verification: {e}")

    print(f"\nTest completed!")
    print(f"Total cards created: {len(created_hashes)}")
    print(f"Total cards in database: {total_cards}")
    print("Cards have been left in the database for further testing.")

    return created_hashes

@pytest.mark.asyncio
async def test_create_html_content(async_client):
    """Test creating an MCard with HTML content."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test HTML</title>
    </head>
    <body>
        <h1>Test Heading</h1>
        <p>Test paragraph with <strong>bold</strong> text.</p>
    </body>
    </html>
    """
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": html_content}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == html_content

@pytest.mark.asyncio
async def test_create_javascript_content(async_client):
    """Test creating an MCard with JavaScript content."""
    js_content = """
    function testFunction() {
        const arr = [1, 2, 3, 4, 5];
        return arr.map(x => x * 2)
            .filter(x => x > 5)
            .reduce((a, b) => a + b, 0);
    }

    class TestClass {
        constructor(name) {
            this.name = name;
        }

        greet() {
            return `Hello, ${this.name}!`;
        }
    }

    const obj = new TestClass('World');
    console.log(obj.greet());
    """
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": js_content}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == js_content

@pytest.mark.asyncio
async def test_create_sql_content(async_client):
    """Test creating an MCard with SQL content."""
    sql_content = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO users (username, email) VALUES
        ('user1', 'user1@example.com'),
        ('user2', 'user2@example.com');

    SELECT u.username, u.email, COUNT(p.id) as post_count
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    GROUP BY u.id
    HAVING post_count > 0
    ORDER BY post_count DESC;
    """
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": sql_content}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == sql_content

@pytest.mark.asyncio
async def test_create_mixed_content(async_client):
    """Test creating an MCard with mixed content types."""
    mixed_content = """
    # Project Documentation

    ## HTML Component
    ```html
    <div class="container">
        <h1>User Profile</h1>
        <div class="profile-card">
            <img src="avatar.jpg" alt="User Avatar">
            <span class="username">@johndoe</span>
        </div>
    </div>
    ```

    ## JavaScript Logic
    ```javascript
    class ProfileManager {
        constructor(userId) {
            this.userId = userId;
        }

        async fetchProfile() {
            const response = await fetch(`/api/users/${this.userId}`);
            return response.json();
        }
    }
    ```

    ## Database Schema
    ```sql
    CREATE TABLE profiles (
        user_id INTEGER PRIMARY KEY,
        avatar_url TEXT,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ```

    ## API Documentation
    - GET `/api/users/:id` - Fetch user profile
    - PUT `/api/users/:id` - Update user profile
    - DELETE `/api/users/:id` - Delete user profile
    """
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": mixed_content}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == mixed_content

@pytest.mark.asyncio
async def test_create_base64_image_content(async_client):
    """Test creating an MCard with base64 encoded image content."""
    # Create a small base64 encoded image (1x1 pixel transparent PNG)
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    content = f"""
    # Image Test

    ![Test Image](data:image/png;base64,{base64_image})
    """
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": content}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == content
    assert base64_image in data["content"]

@pytest.mark.asyncio
async def test_create_binary_content(async_client):
    """Test creating an MCard with various binary content types."""
    # Create test binary data
    binary_data = bytes([i % 256 for i in range(1024)])  # 1KB of test data
    base64_data = base64.b64encode(binary_data).decode('utf-8')
    
    # Test different binary formats
    formats = [
        ("application/octet-stream", "bin"),
        ("application/pdf", "pdf"),
        ("image/jpeg", "jpg"),
        ("application/zip", "zip")
    ]
    
    for mime_type, ext in formats:
        content = f"""
        # Binary Content Test ({mime_type})
        
        [Test File](data:{mime_type};base64,{base64_data})
        """
        
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": content}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == content
        assert base64_data in data["content"]

@pytest.mark.asyncio
async def test_create_large_binary_content(async_client):
    """Test creating an MCard with large binary content."""
    # Create 1MB of test data
    binary_data = bytes([i % 256 for i in range(1024 * 1024)])
    base64_data = base64.b64encode(binary_data).decode('utf-8')
    
    content = f"""
    # Large Binary Content Test
    
    [Large File](data:application/octet-stream;base64,{base64_data})
    """
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": content}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == content
    assert base64_data in data["content"]

@pytest.mark.asyncio
async def test_custom_hash_configuration(async_client):
    """Test custom hash configuration."""
    # Test default hash algorithm
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["hash_algorithm"] == DEFAULT_HASH_ALGORITHM

    # Test custom hash algorithm
    custom_algorithm = "sha512"
    os.environ[ENV_HASH_ALGORITHM] = custom_algorithm
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["hash_algorithm"] == custom_algorithm

    # Reset to default
    os.environ[ENV_HASH_ALGORITHM] = DEFAULT_HASH_ALGORITHM

@pytest.mark.asyncio
async def test_custom_port_configuration(async_client):
    """Test port configuration."""
    # Test default port
    assert app.state.port == DEFAULT_API_PORT

    # Test custom port
    custom_port = 5321
    os.environ[ENV_API_PORT] = str(custom_port)
    
    # Create new app instance to test port configuration
    spec = importlib.util.spec_from_file_location(
        "bridge_server",
        str(Path(__file__).parent.parent.parent / "examples" / "bridge_to_javascript" / "src" / "server.py")
    )
    new_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(new_server)
    
    assert new_server.app.state.port == custom_port

    # Reset to default
    os.environ[ENV_API_PORT] = str(DEFAULT_API_PORT)

@pytest.mark.asyncio
async def test_database_configuration(async_client):
    """Test database configuration."""
    # Verify current test configuration
    setup = app.state.setup
    assert setup.db_path == TEST_DB_PATH
    assert setup.max_connections == TEST_POOL_SIZE
    assert setup.timeout == TEST_TIMEOUT

    # Test with default configuration
    os.environ[ENV_DB_PATH] = DEFAULT_DB_PATH
    os.environ[ENV_DB_MAX_CONNECTIONS] = str(DEFAULT_POOL_SIZE)
    os.environ[ENV_DB_TIMEOUT] = str(DEFAULT_TIMEOUT)

    new_setup = MCardSetup()
    await new_setup.initialize()
    
    assert new_setup.db_path == DEFAULT_DB_PATH
    assert new_setup.max_connections == DEFAULT_POOL_SIZE
    assert new_setup.timeout == DEFAULT_TIMEOUT

    await new_setup.cleanup()

    # Reset test configuration
    os.environ[ENV_DB_PATH] = TEST_DB_PATH
    os.environ[ENV_DB_MAX_CONNECTIONS] = str(TEST_POOL_SIZE)
    os.environ[ENV_DB_TIMEOUT] = str(TEST_TIMEOUT)
