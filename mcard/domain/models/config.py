"""Configuration domain models."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class HashingSettings:
    """Settings for content hashing."""
    algorithm: str = "sha256"
    custom_module: Optional[str] = None
    custom_function: Optional[str] = None
    custom_hash_length: Optional[int] = None

@dataclass
class DatabaseSettings:
    """Settings for database configuration."""
    db_path: str
    max_connections: int = 5
    timeout: float = 30.0
    data_source: str = "sqlite"

@dataclass
class AppSettings:
    """Application settings."""
    database: DatabaseSettings
    hashing: HashingSettings
    mcard_api_key: Optional[str] = None
    mcard_api_port: Optional[int] = None
