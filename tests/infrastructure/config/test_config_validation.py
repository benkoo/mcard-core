"""Tests for configuration validation."""
import os
import pytest
from mcard.infrastructure.config import (
    DataEngineConfig,
    load_config,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_HASH_CUSTOM_LENGTH,
    ENV_HASH_ALGORITHM,
    ENV_HASH_CUSTOM_MODULE,
    ENV_HASH_CUSTOM_FUNCTION,
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

@pytest.mark.parametrize("invalid_value", ["0", "-1", "abc", ""])
def test_invalid_max_connections(setup_test_env, invalid_value):
    """Test handling of invalid max_connections values."""
    os.environ[ENV_DB_MAX_CONNECTIONS] = invalid_value
    with pytest.raises(ValueError):
        load_config()

@pytest.mark.parametrize("invalid_value", ["0", "-1.5", "abc", ""])
def test_invalid_timeout(setup_test_env, invalid_value):
    """Test handling of invalid timeout values."""
    os.environ[ENV_DB_TIMEOUT] = invalid_value
    with pytest.raises(ValueError):
        load_config()

@pytest.mark.parametrize("invalid_value", ["-1", "abc", ""])
def test_invalid_hash_length(setup_test_env, invalid_value):
    """Test handling of invalid hash length values."""
    os.environ[ENV_HASH_CUSTOM_LENGTH] = invalid_value
    with pytest.raises(ValueError):
        load_config()

def test_custom_hash_validation(setup_test_env):
    """Test validation of custom hash configuration."""
    os.environ[ENV_HASH_ALGORITHM] = "custom"
    
    # Test missing custom module
    with pytest.raises(ValueError, match="Custom hash module must be specified"):
        load_config()
    
    # Test missing custom function
    os.environ[ENV_HASH_CUSTOM_MODULE] = "my_module"
    with pytest.raises(ValueError, match="Custom hash function must be specified"):
        load_config()

@pytest.mark.parametrize("algorithm", ["md5", "sha1", "sha224", "sha256", "sha384", "sha512", "custom"])
def test_valid_hash_algorithms(setup_test_env, algorithm):
    """Test all supported hash algorithms."""
    os.environ[ENV_HASH_ALGORITHM] = algorithm
    if algorithm == "custom":
        os.environ[ENV_HASH_CUSTOM_MODULE] = "my_module"
        os.environ[ENV_HASH_CUSTOM_FUNCTION] = "my_function"
    config = load_config()
    assert config.hashing.algorithm == algorithm
