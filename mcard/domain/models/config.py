"""Configuration domain models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

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
    parallel_algorithms: Optional[List[str]] = field(default=None)  # List of algorithms to run in parallel
    verify_parallel: bool = False  # Whether to verify parallel hashes on collision
    max_parallel: int = 3  # Maximum number of parallel algorithms allowed
    
    def __post_init__(self):
        """Validate settings after initialization."""
        if self.algorithm not in HashAlgorithm.__members__.values():
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
            
        if self.algorithm == HashAlgorithm.CUSTOM:
            if not self.custom_module or not self.custom_function:
                raise ValueError("Custom module and function must be specified for custom algorithm")
            if not self.custom_hash_length or self.custom_hash_length <= 0:
                raise ValueError("Custom hash length must be positive")
                
        if self.parallel_algorithms:
            if len(self.parallel_algorithms) > self.max_parallel:
                raise ValueError(f"Too many parallel algorithms specified (max {self.max_parallel})")
            for algo in self.parallel_algorithms:
                if algo not in HashAlgorithm.__members__.values():
                    raise ValueError(f"Unsupported parallel algorithm: {algo}")

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
