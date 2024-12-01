"""Repository configuration domain models."""
from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto
from mcard.infrastructure.persistence.engine_config import EngineConfig, SQLiteConfig
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore

class RepositoryType(Enum):
    """Type of repository."""
    SQLITE = auto()

@dataclass
class RepositoryConfig:
    """Repository configuration."""
    sqlite: Optional[SQLiteConfig] = None
