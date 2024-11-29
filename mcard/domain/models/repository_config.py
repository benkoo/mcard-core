"""Repository configuration domain models."""
from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto

class RepositoryType(Enum):
    """Type of repository."""
    SQLITE = auto()

@dataclass
class SQLiteConfig:
    """SQLite repository configuration."""
    db_path: str
    type: RepositoryType = RepositoryType.SQLITE
    pool_size: int = 5
    timeout: float = 30.0
    max_content_size: int = 10 * 1024 * 1024  # 10MB default
    
@dataclass
class RepositoryConfig:
    """Repository configuration."""
    sqlite: Optional[SQLiteConfig] = None
