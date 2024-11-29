"""Tests for configuration models."""
import pytest
from mcard.domain.models.config import (
    AppSettings, HashingSettings,
    HashAlgorithm
)
from mcard.domain.models.repository_config import (
    RepositoryConfig, SQLiteConfig, RepositoryType
)

def test_sqlite_config_defaults():
    """Test SQLiteConfig with default values."""
    settings = SQLiteConfig(db_path="test.db")
    assert settings.db_path == "test.db"
    assert settings.pool_size == 5
    assert settings.timeout == 30.0
    assert settings.max_content_size == 10 * 1024 * 1024  # 10MB

def test_sqlite_config_custom():
    """Test SQLiteConfig with custom values."""
    settings = SQLiteConfig(
        db_path="test.db",
        pool_size=10,
        timeout=60.0,
        max_content_size=20 * 1024 * 1024  # 20MB
    )
    assert settings.db_path == "test.db"
    assert settings.pool_size == 10
    assert settings.timeout == 60.0
    assert settings.max_content_size == 20 * 1024 * 1024

def test_hashing_settings_defaults():
    """Test HashingSettings with default values."""
    settings = HashingSettings()
    assert settings.algorithm == "sha256"
    assert settings.custom_module is None
    assert settings.custom_function is None
    assert settings.custom_hash_length is None

def test_hashing_settings_custom():
    """Test HashingSettings with custom values."""
    settings = HashingSettings(algorithm="sha512")
    assert settings.algorithm == "sha512"

def test_app_settings_defaults():
    """Test AppSettings with default values."""
    settings = AppSettings(
        repository=SQLiteConfig(db_path="test.db"),
        mcard_api_key="test_api_key"
    )
    assert isinstance(settings.repository, SQLiteConfig)
    assert settings.repository.db_path == "test.db"
    assert settings.hashing.algorithm == "sha256"

def test_app_settings_custom():
    """Test AppSettings with custom values."""
    settings = AppSettings(
        repository=SQLiteConfig(
            db_path="test.db",
            pool_size=10,
            timeout=60.0,
            max_content_size=20 * 1024 * 1024
        ),
        hashing=HashingSettings(algorithm="sha512"),
        mcard_api_key="test_api_key"
    )
    assert isinstance(settings.repository, SQLiteConfig)
    assert settings.repository.db_path == "test.db"
    assert settings.repository.pool_size == 10
    assert settings.repository.timeout == 60.0
    assert settings.repository.max_content_size == 20 * 1024 * 1024
    assert settings.hashing.algorithm == "sha512"

def test_invalid_hash_function():
    """Test that invalid hash functions are rejected."""
    with pytest.raises(ValueError):
        HashingSettings(algorithm="invalid")

def test_custom_hash_settings():
    """Test custom hash function settings."""
    settings = HashingSettings(
        algorithm="custom",
        custom_module="my_hash_module",
        custom_function="my_hash_function",
        custom_hash_length=64
    )
    assert settings.algorithm == "custom"
    assert settings.custom_module == "my_hash_module"
    assert settings.custom_function == "my_hash_function"
    assert settings.custom_hash_length == 64
