"""Tests for default configuration behavior."""
import os
import sys
import tempfile
import subprocess
import pytest
from pathlib import Path
from mcard.infrastructure.config import (
    DataEngineConfig,
    load_config,
    get_test_db_path,
)

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

def test_default_config(setup_test_env):
    """Test default configuration values."""
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
        env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        env['MCARD_FORCE_DEFAULT_CONFIG'] = 'true'
        
        # Use the project root as the working directory
        cwd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        result = subprocess.run([sys.executable, f.name], env=env, cwd=cwd, capture_output=True, text=True)
        
        # Check if the script ran successfully
        assert result.returncode == 0, f"Script failed with:\n{result.stderr}"

def test_test_mode_config(setup_test_env):
    """Test configuration in test mode (PYTEST_CURRENT_TEST set)."""
    os.environ['PYTEST_CURRENT_TEST'] = "test_something"
    config = load_config()
    assert config.repository.db_path == str(get_test_db_path())
    assert config.repository.max_connections == 5
    assert config.repository.timeout == 30.0
    assert config.hashing.algorithm == "sha256"
