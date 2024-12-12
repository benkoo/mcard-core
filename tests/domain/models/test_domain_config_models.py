"""Tests for domain configuration models."""
import pytest
from mcard.domain.models.domain_config_models import (
    HashAlgorithm,
    HashingSettings,
    DatabaseSettings,
)

def test_database_settings_defaults():
    """Test DatabaseSettings default values."""
    settings = DatabaseSettings(db_path="/path/to/db")
    assert settings.db_path == "/path/to/db"
    assert settings.max_connections == 5
    assert settings.timeout == 30.0
    assert settings.data_source == "sqlite"

def test_database_settings_custom():
    """Test DatabaseSettings with custom values."""
    settings = DatabaseSettings(
        db_path="/path/to/db",
        max_connections=10,
        timeout=60.0,
        data_source="custom"
    )
    assert settings.db_path == "/path/to/db"
    assert settings.max_connections == 10
    assert settings.timeout == 60.0
    assert settings.data_source == "custom"

def test_hashing_settings_defaults():
    """Test HashingSettings default values."""
    settings = HashingSettings()
    assert settings.algorithm == "sha256"
    assert settings.custom_module is None
    assert settings.custom_function is None
    assert settings.custom_hash_length is None
    assert settings.parallel_algorithms is None
    assert settings.verify_parallel is False
    assert settings.max_parallel == 3

def test_hashing_settings_custom():
    """Test HashingSettings with custom values."""
    settings = HashingSettings(
        algorithm="sha512",
        custom_module="my_module",
        custom_function="my_function",
        custom_hash_length=64,
        parallel_algorithms=["sha256", "sha512"],
        verify_parallel=True,
        max_parallel=5
    )
    assert settings.algorithm == "sha512"
    assert settings.custom_module == "my_module"
    assert settings.custom_function == "my_function"
    assert settings.custom_hash_length == 64
    assert settings.parallel_algorithms == ["sha256", "sha512"]
    assert settings.verify_parallel is True
    assert settings.max_parallel == 5

def test_hashing_settings_validation():
    """Test HashingSettings validation."""
    # Test invalid algorithm
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        HashingSettings(algorithm="invalid")

    # Test invalid parallel algorithms
    with pytest.raises(ValueError, match="Unsupported parallel algorithm"):
        HashingSettings(parallel_algorithms=["sha256", "invalid"])

    # Test custom hash without module/function
    with pytest.raises(ValueError, match="Custom hash requires both module and function"):
        HashingSettings(algorithm="custom")

    # Test custom hash with only module
    with pytest.raises(ValueError, match="Custom hash requires both module and function"):
        HashingSettings(algorithm="custom", custom_module="my_module")

    # Test custom hash with only function
    with pytest.raises(ValueError, match="Custom hash requires both module and function"):
        HashingSettings(algorithm="custom", custom_function="my_function")
