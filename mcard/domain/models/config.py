"""Configuration domain models."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class HashAlgorithm(str, Enum):
    """Supported hash algorithms."""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA224 = "sha224"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    CUSTOM = "custom"

@dataclass
class HashingSettings:
    """Settings for content hashing."""
    algorithm: str = "sha256"
    custom_module: Optional[str] = None
    custom_function: Optional[str] = None
    custom_hash_length: Optional[int] = None

@dataclass
class SQLiteConfig:
    """Configuration for SQLite database."""
    db_path: str
    pool_size: int = 5
    timeout: float = 30.0
    max_connections: int = 5

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
