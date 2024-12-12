"""Tests for database engine configuration."""
import pytest
from mcard.infrastructure.persistence.database_engine_config import (
    EngineConfig,
    SQLiteConfig,
    EngineType,
    DatabaseType,
    create_engine_config
)

def test_sqlite_config_defaults():
    """Test SQLiteConfig default values."""
    config = SQLiteConfig(db_path=":memory:")
    assert config.engine_type == EngineType.SQLITE
    assert config.connection_string == ":memory:"
    assert config.max_connections == 5
    assert config.timeout == 5.0
    assert config.max_content_size == 5 * 1024 * 1024
    assert config.engine_options == {"check_same_thread": False}

def test_sqlite_config_custom():
    """Test SQLiteConfig with custom values."""
    config = SQLiteConfig(
        db_path="/path/to/db",
        max_connections=10,
        timeout=60.0,
        max_content_size=10 * 1024 * 1024,
        check_same_thread=True
    )
    assert config.engine_type == EngineType.SQLITE
    assert config.connection_string == "/path/to/db"
    assert config.max_connections == 10
    assert config.timeout == 60.0
    assert config.max_content_size == 10 * 1024 * 1024
    assert config.engine_options == {"check_same_thread": True}

def test_sqlite_config_validation():
    """Test SQLiteConfig validation."""
    # Test invalid max_connections
    with pytest.raises(ValueError, match="max_connections must be positive"):
        SQLiteConfig(db_path=":memory:", max_connections=0)

    # Test invalid timeout
    with pytest.raises(ValueError, match="timeout must be positive"):
        SQLiteConfig(db_path=":memory:", timeout=-1.0)

    # Test invalid max_content_size
    with pytest.raises(ValueError, match="max_content_size must be positive"):
        SQLiteConfig(db_path=":memory:", max_content_size=0)

def test_create_engine_config():
    """Test create_engine_config factory function."""
    # Test creating SQLite config
    config = create_engine_config(
        engine_type=EngineType.SQLITE,
        connection_string=":memory:",
        max_connections=10,
        timeout=60.0
    )
    assert isinstance(config, SQLiteConfig)
    assert config.engine_type == EngineType.SQLITE
    assert config.connection_string == ":memory:"
    assert config.max_connections == 10
    assert config.timeout == 60.0

    # Test invalid engine type
    with pytest.raises(ValueError, match="Unsupported engine type"):
        create_engine_config(
            engine_type="invalid",
            connection_string=":memory:"
        )
