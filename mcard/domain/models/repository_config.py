"""Repository configuration domain models."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class SQLiteConfig:
    """SQLite repository configuration."""
    database_path: str
    
@dataclass
class RepositoryConfig:
    """Repository configuration."""
    sqlite: Optional[SQLiteConfig] = None
