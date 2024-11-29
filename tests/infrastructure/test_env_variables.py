import os
import pytest
from dotenv import load_dotenv
from pathlib import Path

# Load test-specific environment variables
test_env_path = Path(__file__).parent.parent / '.env.test'
load_dotenv(test_env_path, override=True)  # Add override=True to ensure test values take precedence


def test_mcard_api_key_from_env():
    """Test if MCARD_API_KEY is correctly loaded from the .env file."""
    expected_api_key = 'test_custom_api_key_12345'  # Match the API key used in other tests
    actual_api_key = os.getenv('MCARD_API_KEY')
    assert actual_api_key == expected_api_key, f"Expected MCARD_API_KEY to be '{expected_api_key}', but got '{actual_api_key}'"


def test_mcard_api_key_not_set():
    """Test behavior when MCARD_API_KEY is not set."""
    # Temporarily remove MCARD_API_KEY from environment
    original_key = os.environ.pop('MCARD_API_KEY', None)
    try:
        assert os.getenv('MCARD_API_KEY') is None
    finally:
        # Restore original API key
        if original_key is not None:
            os.environ['MCARD_API_KEY'] = original_key


def test_mcard_store_db_path():
    """Test if MCARD_STORE_DB_PATH is correctly loaded and relative to project root."""
    expected_db_path = 'data/test_mcard.db'
    actual_db_path = os.getenv('MCARD_STORE_DB_PATH')
    assert actual_db_path == expected_db_path, f"Expected MCARD_STORE_DB_PATH to be '{expected_db_path}', but got '{actual_db_path}'"

    # Verify the path exists and is relative to project root
    from mcard.infrastructure.config import get_project_root
    db_path = get_project_root() / expected_db_path
    assert db_path.parent.exists(), f"Database directory {db_path.parent} does not exist"
    assert db_path.parent.is_dir(), f"{db_path.parent} is not a directory"


def test_data_directory_creation():
    """Test that the data directory is created if it doesn't exist."""
    from mcard.infrastructure.config import get_project_root, get_default_db_path, get_test_db_path
    
    # Get data directory path
    data_dir = get_project_root() / "data"
    
    # Remove data directory if it exists
    if data_dir.exists():
        import shutil
        shutil.rmtree(data_dir)
    
    # Verify directory doesn't exist
    assert not data_dir.exists()
    
    # Get database paths (this should create the data directory)
    default_db = get_default_db_path()
    test_db = get_test_db_path()
    
    # Verify directory was created
    assert data_dir.exists()
    assert data_dir.is_dir()
    
    # Verify database paths are correct
    assert default_db == data_dir / "mcard.db"
    assert test_db == data_dir / "test_mcard.db"


def test_test_mode_configuration():
    """Test that test-specific configuration is used in test mode."""
    import os
    from mcard.infrastructure.config import load_config, get_test_db_path
    from mcard.infrastructure.persistence.store import MCardStore
    
    # Set test mode
    os.environ['PYTEST_CURRENT_TEST'] = 'test_test_mode_configuration'
    
    try:
        # Initialize store with test configuration
        store = MCardStore()
        store.configure()
        
        # Verify test-specific database path is used
        expected_db_path = str(get_test_db_path())
        assert store._config.engine_config.connection_string == expected_db_path, \
            f"Expected test database path '{expected_db_path}', but got '{store._config.engine_config.connection_string}'"
        
        # Verify other test defaults through the config
        config = load_config()
        assert config.hashing.algorithm == "sha256", "Unexpected hash algorithm"
        assert config.hashing.custom_module is None, "Custom hash module should be None"
        assert config.hashing.custom_function is None, "Custom hash function should be None"
        assert config.hashing.custom_length is None, "Custom hash length should be None"
    finally:
        # Clean up test mode
        del os.environ['PYTEST_CURRENT_TEST']
        # Reset store singleton
        MCardStore._instance = None
        MCardStore._initialized = False


def test_env_overrides_in_test_mode():
    """Test that environment variables can override test defaults."""
    import os
    from mcard.infrastructure.config import load_config, ENV_DB_PATH, ENV_DB_MAX_CONNECTIONS, ENV_DB_TIMEOUT
    
    # Set test mode
    os.environ['PYTEST_CURRENT_TEST'] = 'test_env_overrides_in_test_mode'
    
    # Set custom environment variables
    custom_config = {
        ENV_DB_PATH: 'data/custom_test.db',
        ENV_DB_MAX_CONNECTIONS: '15',
        ENV_DB_TIMEOUT: '45.0'
    }
    
    # Store original values
    original_values = {key: os.getenv(key) for key in custom_config}
    
    try:
        # Set custom values
        for key, value in custom_config.items():
            os.environ[key] = value
        
        # Load configuration
        config = load_config()
        
        # Verify environment variables override test defaults
        assert config.repository.db_path == 'data/custom_test.db', "DB path override failed"
        assert config.repository.max_connections == 15, "Max connections override failed"
        assert config.repository.timeout == 45.0, "Timeout override failed"
    
    finally:
        # Restore original environment
        for key, value in original_values.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value
        del os.environ['PYTEST_CURRENT_TEST']
