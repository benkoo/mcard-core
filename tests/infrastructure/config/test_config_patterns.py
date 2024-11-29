"""Tests for configuration design patterns and architecture."""
import os
import pytest
from mcard.infrastructure.config import (
    DataEngineConfig,
    EnvironmentConfigSource,
    TestConfigSource,
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

def test_singleton_pattern():
    """Test that DataEngineConfig follows the singleton pattern."""
    config1 = DataEngineConfig.get_instance()
    config2 = DataEngineConfig.get_instance()
    assert config1 is config2

def test_configuration_source_strategy():
    """Test that different configuration sources can be used."""
    # Test with environment source
    config = DataEngineConfig.get_instance()
    source = EnvironmentConfigSource()
    config.configure(source)
    assert isinstance(source, EnvironmentConfigSource)
    
    # Test with test source
    DataEngineConfig.reset()
    config = DataEngineConfig.get_instance()
    source = TestConfigSource()
    config.configure(source)
    assert isinstance(source, TestConfigSource)

def test_configuration_immutability():
    """Test that configuration cannot be modified after initialization."""
    config = DataEngineConfig.get_instance()
    source = EnvironmentConfigSource()
    config.configure(source)
    
    # Attempt to reconfigure should raise an error
    with pytest.raises(RuntimeError, match="Configuration is already initialized"):
        config.configure(TestConfigSource())
