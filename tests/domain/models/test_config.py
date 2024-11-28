"""Tests for configuration models."""
import pytest
from mcard.domain.models.config import (
    AppSettings, DatabaseSettings, HashingSettings,
    HashAlgorithm
)

def test_database_settings_defaults():
    """Test DatabaseSettings with default values."""
    settings = DatabaseSettings(db_path="test.db")
    assert settings.db_path == "test.db"
    assert settings.data_source is None
    assert settings.pool_size == 5
    assert settings.timeout == 30.0

def test_database_settings_custom():
    """Test DatabaseSettings with custom values."""
    settings = DatabaseSettings(
        db_path="test.db",
        data_source="source",
        pool_size=10,
        timeout=60.0
    )
    assert settings.db_path == "test.db"
    assert settings.data_source == "source"
    assert settings.pool_size == 10
    assert settings.timeout == 60.0

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
    settings = AppSettings(database=DatabaseSettings(db_path="test.db"), mcard_api_key="test_api_key")
    assert settings.database.db_path == "test.db"
    assert settings.hashing.algorithm == "sha256"

def test_app_settings_custom():
    """Test AppSettings with custom values."""
    settings = AppSettings(
        database=DatabaseSettings(
            db_path="custom.db",
            pool_size=15
        ),
        hashing=HashingSettings(algorithm="sha512"),
        mcard_api_key="custom_api_key"
    )
    assert settings.database.db_path == "custom.db"
    assert settings.database.pool_size == 15
    assert settings.hashing.algorithm == "sha512"

def test_invalid_hash_function():
    """Test that invalid hash functions are rejected."""
    with pytest.raises(ValueError):
        HashingSettings(algorithm="invalid")  # type: ignore

def test_custom_hash_settings():
    """Test custom hash function settings."""
    settings = HashingSettings(
        algorithm="custom",
        custom_module="hashlib",
        custom_function="sha256",
        custom_hash_length=64
    )
    assert settings.algorithm == "custom"
    assert settings.custom_module == "hashlib"
    assert settings.custom_function == "sha256"
    assert settings.custom_hash_length == 64
