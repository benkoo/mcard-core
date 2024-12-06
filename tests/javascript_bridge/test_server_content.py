"""Test suite for content handling in MCard JavaScript bridge server.

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
import base64
import random
from mcard.infrastructure.setup import MCardSetup
from mcard.config_constants import (
    DEFAULT_POOL_SIZE,
    DEFAULT_TIMEOUT,
    DEFAULT_API_PORT,
    ENV_DB_PATH,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_API_PORT,
    ENV_HASH_ALGORITHM,
    DEFAULT_HASH_ALGORITHM,
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
TEST_POOL_SIZE = DEFAULT_POOL_SIZE * 2
TEST_TIMEOUT = DEFAULT_TIMEOUT

@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    original_env = {
        "MCARD_API_KEY": os.environ.get("MCARD_API_KEY"),
        ENV_DB_PATH: os.environ.get(ENV_DB_PATH),
        ENV_DB_MAX_CONNECTIONS: os.environ.get(ENV_DB_MAX_CONNECTIONS),
        ENV_DB_TIMEOUT: os.environ.get(ENV_DB_TIMEOUT),
        ENV_API_PORT: os.environ.get(ENV_API_PORT),
        ENV_HASH_ALGORITHM: os.environ.get(ENV_HASH_ALGORITHM),
    }
    
    os.environ["MCARD_API_KEY"] = TEST_API_KEY
    os.environ[ENV_DB_PATH] = TEST_DB_PATH
    os.environ[ENV_DB_MAX_CONNECTIONS] = str(TEST_POOL_SIZE)
    os.environ[ENV_DB_TIMEOUT] = str(TEST_TIMEOUT)
    os.environ[ENV_API_PORT] = str(DEFAULT_API_PORT)
    os.environ[ENV_HASH_ALGORITHM] = DEFAULT_HASH_ALGORITHM
    
    yield
    
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Setup test database."""
    Path(TEST_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        Path(TEST_DB_PATH).unlink(missing_ok=True)
    except Exception:
        pass
        
    setup = MCardSetup(
        db_path=TEST_DB_PATH,
        max_connections=TEST_POOL_SIZE,
        timeout=TEST_TIMEOUT
    )
    
    await setup.initialize()
    app.state.setup = setup
    
    yield
    
    await setup.cleanup()
    try:
        Path(TEST_DB_PATH).unlink(missing_ok=True)
    except Exception:
        pass

@pytest.fixture
async def async_client():
    """Create async client for testing."""
    app.state.api_key = TEST_API_KEY
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

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
        <h1>Hello, World!</h1>
        <p>This is a test HTML document.</p>
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
    function calculateFactorial(n) {
        if (n === 0 || n === 1) {
            return 1;
        }
        return n * calculateFactorial(n - 1);
    }

    class Calculator {
        constructor() {
            this.value = 0;
        }
        
        add(x) {
            this.value += x;
            return this;
        }
        
        multiply(x) {
            this.value *= x;
            return this;
        }
        
        getResult() {
            return this.value;
        }
    }
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

    CREATE INDEX idx_username ON users(username);
    CREATE INDEX idx_email ON users(email);

    INSERT INTO users (username, email) VALUES
        ('john_doe', 'john@example.com'),
        ('jane_doe', 'jane@example.com');
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
    # Python code
    def process_data():
        return {"status": "success"}

    # JavaScript code
    function handleResponse(data) {
        console.log(data.status);
    }

    <!-- HTML markup -->
    <div class="container">
        <h1>Results</h1>
        <pre id="output"></pre>
    </div>

    /* CSS styles */
    .container {
        margin: 20px;
        padding: 10px;
        border: 1px solid #ccc;
    }

    # SQL query
    SELECT * FROM results WHERE status = 'success';
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
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": base64_image}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == base64_image

@pytest.mark.asyncio
async def test_create_binary_content(async_client):
    """Test creating an MCard with various binary content types."""
    # Create random binary data
    binary_sizes = [1024, 2048, 4096]  # Test different sizes
    for size in binary_sizes:
        binary_data = bytes([random.randint(0, 255) for _ in range(size)])
        base64_data = base64.b64encode(binary_data).decode('utf-8')
        
        response = await async_client.post(
            "/cards",
            headers={"X-API-Key": TEST_API_KEY},
            json={"content": base64_data}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == base64_data
        
        # Verify we can retrieve the content
        get_response = await async_client.get(
            f"/cards/{data['hash']}",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert get_response.status_code == 200
        assert get_response.json()["content"] == base64_data

@pytest.mark.asyncio
async def test_create_large_binary_content(async_client):
    """Test creating an MCard with large binary content."""
    # Create a 1MB binary file
    size = 1024 * 1024  # 1MB
    binary_data = bytes([random.randint(0, 255) for _ in range(size)])
    base64_data = base64.b64encode(binary_data).decode('utf-8')
    
    response = await async_client.post(
        "/cards",
        headers={"X-API-Key": TEST_API_KEY},
        json={"content": base64_data}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == base64_data
