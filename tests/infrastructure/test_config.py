"""Tests for configuration management.

This module provides comprehensive testing for the configuration management system,
including environment variable loading, default values, and error handling.
"""
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from mcard.infrastructure.config import (
    DataEngineConfig, 
    load_config, 
    get_default_db_path,
    get_test_db_path,
    ENV_DB_PATH,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_HASH_ALGORITHM,
    ENV_HASH_CUSTOM_MODULE,
    ENV_HASH_CUSTOM_FUNCTION,
    ENV_HASH_CUSTOM_LENGTH,
    EnvironmentConfigSource,
    TestConfigSource,
)
from mcard.domain.dependency.hashing import HashingSettings
from pytest_mock import mocker

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment before each test."""
    # Store original environment variables
    original_env = {key: value for key, value in os.environ.items()}
    
    # Clear all environment variables
    os.environ.clear()
    
    # Restore only non-test environment variables
    for key, value in original_env.items():
        if not key.startswith('MCARD_') and key != 'PYTEST_CURRENT_TEST':
            os.environ[key] = value
    
    # Reset singleton
    DataEngineConfig.reset()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    
    # Reset singleton
    DataEngineConfig.reset()

@pytest.fixture
def clean_env():
    """Clean environment variables before each test."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Clear all environment variables
    os.environ.clear()
    
    # Restore only non-test environment variables
    for key, value in original_env.items():
        if not key.startswith('MCARD_') and key != 'PYTEST_CURRENT_TEST':
            os.environ[key] = value
    
    # Ensure we're not in test mode
    if 'PYTEST_CURRENT_TEST' in os.environ:
        del os.environ['PYTEST_CURRENT_TEST']
    
    # Reset singleton
    DataEngineConfig.reset()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    
    # Reset singleton
    DataEngineConfig.reset()

@pytest.fixture
def test_env(tmp_path):
    """Create a test.env file."""
    # Create a test environment file
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
    
    # Load the test environment file
    load_dotenv(env_file)
    
    return env_file

def test_default_config(clean_env):
    """Test default configuration values."""
    # Create a temporary script to run the test
    import tempfile
    import subprocess
    import sys
    
    script = """
import os
from pathlib import Path
from mcard.infrastructure.config import load_config, get_project_root

# Clear any existing MCARD_ environment variables
for key in list(os.environ.keys()):
    if key.startswith('MCARD_'):
        del os.environ[key]

# Set force default config
os.environ['MCARD_FORCE_DEFAULT_CONFIG'] = 'true'

config = load_config()
assert config.repository.db_path == "data/mcard.db", f"Expected data/mcard.db, got {config.repository.db_path}"
assert config.repository.max_connections == 5
assert config.repository.timeout == 30.0
assert config.hashing.algorithm == "sha256"
assert config.hashing.custom_module is None
assert config.hashing.custom_function is None
assert config.hashing.custom_hash_length is None
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
        f.write(script)
        f.flush()
        
        # Run the script in a clean environment
        env = {k: v for k, v in os.environ.items() if not k.startswith('MCARD_') and k != 'PYTEST_CURRENT_TEST'}
        env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env['MCARD_FORCE_DEFAULT_CONFIG'] = 'true'
        
        # Use the project root as the working directory
        cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        result = subprocess.run([sys.executable, f.name], env=env, cwd=cwd, capture_output=True, text=True)
        
        # Check if the script ran successfully
        assert result.returncode == 0, f"Script failed with:\n{result.stderr}"

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

def test_test_mode_config(clean_env):
    """Test configuration in test mode (PYTEST_CURRENT_TEST set)."""
    os.environ['PYTEST_CURRENT_TEST'] = "test_something"
    config = load_config()
    assert config.repository.db_path == str(get_test_db_path())
    assert config.repository.max_connections == 5
    assert config.repository.timeout == 30.0
    assert config.hashing.algorithm == "sha256"

@pytest.mark.parametrize("invalid_value", ["0", "-1", "abc", ""])
def test_invalid_max_connections(clean_env, invalid_value):
    """Test handling of invalid max_connections values."""
    os.environ[ENV_DB_MAX_CONNECTIONS] = invalid_value
    with pytest.raises(ValueError):
        load_config()

@pytest.mark.parametrize("invalid_value", ["0", "-1.5", "abc", ""])
def test_invalid_timeout(clean_env, invalid_value):
    """Test handling of invalid timeout values."""
    os.environ[ENV_DB_TIMEOUT] = invalid_value
    with pytest.raises(ValueError):
        load_config()

@pytest.mark.parametrize("invalid_value", ["-1", "abc", ""])
def test_invalid_hash_length(clean_env, invalid_value):
    """Test handling of invalid hash length values."""
    os.environ[ENV_HASH_CUSTOM_LENGTH] = invalid_value
    with pytest.raises(ValueError):
        load_config()

def test_custom_hash_validation(clean_env):
    """Test validation of custom hash configuration."""
    # Test missing module
    os.environ[ENV_HASH_ALGORITHM] = "custom"
    os.environ[ENV_HASH_CUSTOM_FUNCTION] = "hash_func"
    with pytest.raises(ValueError, match="Custom hash module.*"):
        load_config()
    
    # Clear environment and reset for next test
    os.environ.clear()
    DataEngineConfig.reset()
    
    # Test missing function
    os.environ[ENV_HASH_ALGORITHM] = "custom"
    os.environ[ENV_HASH_CUSTOM_MODULE] = "hash_module"
    with pytest.raises(ValueError, match="Custom hash function.*"):
        load_config()

def test_path_creation(mocker):
    """Test that database paths are created if they don't exist."""
    from mcard.infrastructure.config import get_project_root
    
    # Get the project's data directory
    data_dir = get_project_root() / "data"
    test_db_path = data_dir / "test_creation.db"
    
    # Remove test file if it exists
    if test_db_path.exists():
        test_db_path.unlink()
    
    try:
        mocker.patch.dict(os.environ, {ENV_DB_PATH: str(test_db_path)})
        config = load_config()
        
        # Verify data directory was created
        assert data_dir.exists()
        assert data_dir.is_dir()
        
        # Verify configuration uses correct path
        assert config.repository.db_path == str(test_db_path)
        assert Path(config.repository.db_path).parent == data_dir
    finally:
        # Clean up test file
        if test_db_path.exists():
            test_db_path.unlink()

@pytest.mark.parametrize("algorithm", [
    "md5", "sha1", "sha224", "sha256", "sha384", "sha512", "custom"
])
def test_valid_hash_algorithms(clean_env, algorithm):
    """Test all supported hash algorithms."""
    os.environ[ENV_HASH_ALGORITHM] = algorithm
    if algorithm == "custom":
        os.environ[ENV_HASH_CUSTOM_MODULE] = "test_module"
        os.environ[ENV_HASH_CUSTOM_FUNCTION] = "test_function"
    
    config = load_config()
    assert config.hashing.algorithm == algorithm

def test_singleton_pattern():
    """Test that DataEngineConfig follows the singleton pattern."""
    config1 = DataEngineConfig()
    config2 = DataEngineConfig()
    assert config1 is config2

def test_configuration_source_strategy():
    """Test that different configuration sources can be used."""
    # Test environment source
    env_source = EnvironmentConfigSource()
    env_config = env_source.load()
    assert isinstance(env_config, dict)
    
    # Test test source
    test_source = TestConfigSource()
    test_config = test_source.load()
    assert isinstance(test_config, dict)
    assert test_config['db_path'] == str(get_test_db_path())

def test_configuration_immutability(clean_env):
    """Test that configuration cannot be modified after initialization."""
    config = DataEngineConfig()
    
    # First configuration should succeed
    config.configure(EnvironmentConfigSource())
    
    # Second configuration should fail
    with pytest.raises(RuntimeError, match="Configuration is already initialized"):
        config.configure(TestConfigSource())

def test_load_env_test_file(clean_env):
    """Test loading configuration values from .env.test file."""
    # Load the test environment file
    load_dotenv("tests/.env.test")
    
    config = load_config()
    
    # Verify values from .env.test are loaded correctly
    assert config.repository.db_path == "data/test_mcard.db"
    assert config.repository.max_connections == 10
    assert config.repository.timeout == 60
    assert config.hashing.algorithm == "sha256"
    assert config.hashing.custom_module == "test_module"
    assert config.hashing.custom_function == "test_function"
    assert config.hashing.custom_hash_length == 32

def test_env_file_exists():
    """Test that .env file exists in the project root."""
    root_dir = Path(__file__).parent.parent.parent
    env_file = root_dir / '.env'
    assert env_file.exists(), f".env file not found at {env_file}"

def test_env_test_file_exists():
    """Test that tests/.env.test file exists."""
    root_dir = Path(__file__).parent.parent.parent
    test_env_file = root_dir / 'tests' / '.env.test'
    assert test_env_file.exists(), f"tests/.env.test file not found at {test_env_file}"
