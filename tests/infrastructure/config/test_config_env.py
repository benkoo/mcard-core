"""Tests for environment variable configuration handling."""
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from mcard.infrastructure.config import (
    DataEngineConfig,
    load_config,
    ENV_DB_PATH,
    ENV_HASH_ALGORITHM,
)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment before each test."""
    original_env = {key: value for key, value in os.environ.items()}
    os.environ.clear()
    for key, value in original_env.items():
        if not key.startswith('MCARD_') and key != 'PYTEST_CURRENT_TEST':
            os.environ[key] = value
    DataEngineConfig.reset()
    yield
    os.environ.clear()
    os.environ.update(original_env)
    DataEngineConfig.reset()

@pytest.fixture
def test_env(tmp_path):
    """Create a test.env file."""
    env_file = tmp_path / "test.env"
    env_content = """
    # Database configuration
    MCARD_STORE_DB_PATH=data/test_mcard.db
    MCARD_STORE_MAX_CONNECTIONS=10
    MCARD_STORE_TIMEOUT=60.0
    
    # Hash configuration
    MCARD_HASH_ALGORITHM=sha256
    """
    env_file.write_text(env_content)
    load_dotenv(env_file)
    return env_file

def test_env_file_config(test_env):
    """Test configuration loading from test.env file."""
    config = load_config()
    assert config.repository.db_path == "data/test_mcard.db"
    assert config.repository.max_connections == 10
    assert config.repository.timeout == 60.0
    assert config.hashing.algorithm == "sha256"

def test_env_override(test_env):
    """Test that environment variables override .env file values."""
    # Override some .env values
    os.environ[ENV_DB_PATH] = "/custom/override/path.db"
    os.environ[ENV_HASH_ALGORITHM] = "md5"
    
    config = load_config()
    
    # Check overridden values
    assert config.repository.db_path == "/custom/override/path.db"
    assert config.hashing.algorithm == "md5"
    
    # Check non-overridden values remain from .env
    assert config.repository.max_connections == 10
    assert config.repository.timeout == 60.0

def test_load_env_test_file(setup_test_env):
    """Test loading configuration values from .env.test file."""
    test_env_path = Path(__file__).parent.parent.parent / "tests" / ".env.test"
    load_dotenv(test_env_path)
    config = load_config()
    assert config.repository.db_path == "data/test_mcard.db"
