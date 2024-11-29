"""Database engine configuration module."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class EngineType(Enum):
    """Supported database engine types."""
    SQLITE = "sqlite"
    # Add more engine types as needed
    # POSTGRES = "postgres"
    # MONGODB = "mongodb"


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    # Add more database types as needed
    # POSTGRES = "postgres"
    # MONGODB = "mongodb"


@dataclass
class EngineConfig:
    """Base configuration for database engines."""
    engine_type: EngineType
    connection_string: str
    max_connections: Optional[int] = 5
    timeout: Optional[float] = 5.0
    max_content_size: Optional[int] = 5 * 1024 * 1024  # Default 5MB
    engine_options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.connection_string:
            raise ValueError("Connection string cannot be empty")
        if self.max_connections is not None and self.max_connections <= 0:
            raise ValueError("Maximum connections must be positive")
        if self.timeout is not None and self.timeout < 0:
            raise ValueError("Timeout must be non-negative")
        if self.max_content_size is not None and self.max_content_size <= 0:
            raise ValueError("Maximum content size must be positive")
        self._validate_engine_specific()

    def _validate_engine_specific(self):
        """Validate engine-specific configuration."""
        if self.engine_type == EngineType.SQLITE:
            self._validate_sqlite_config()
        # Add validation for other engine types as needed

    def _validate_sqlite_config(self):
        """Validate SQLite-specific configuration."""
        check_same_thread = self.engine_options.get('check_same_thread')
        if check_same_thread is not None and not isinstance(check_same_thread, bool):
            raise ValueError("check_same_thread must be a boolean")


@dataclass
class SQLiteConfig(EngineConfig):
    """Configuration specific to SQLite database."""
    def __init__(self, 
                 db_path: str,
                 max_connections: Optional[int] = 5,
                 timeout: Optional[float] = 5.0,
                 check_same_thread: Optional[bool] = False,
                 max_content_size: Optional[int] = 5 * 1024 * 1024):
        """Initialize SQLite configuration."""
        super().__init__(
            engine_type=EngineType.SQLITE,
            connection_string=db_path,
            max_connections=max_connections,
            timeout=timeout,
            max_content_size=max_content_size,
            engine_options={'check_same_thread': check_same_thread}
        )

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self.connection_string

    @property
    def check_same_thread(self) -> bool:
        """Get the check_same_thread setting."""
        return self.engine_options.get('check_same_thread', False)


# Factory function to create appropriate config
def create_engine_config(engine_type: EngineType, **kwargs) -> EngineConfig:
    """Create an engine configuration based on the engine type."""
    if engine_type == EngineType.SQLITE:
        return SQLiteConfig(
            db_path=kwargs.get('connection_string') or kwargs.get('db_path'),
            max_connections=kwargs.get('max_connections', 5),
            timeout=kwargs.get('timeout', 5.0),
            check_same_thread=kwargs.get('check_same_thread', False),
            max_content_size=kwargs.get('max_content_size', 5 * 1024 * 1024)
        )
    # Add support for other engine types as needed
    raise ValueError(f"Unsupported engine type: {engine_type}")
