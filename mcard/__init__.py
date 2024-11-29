"""
MCard Core: A content-addressable data wrapper library.
"""

from .domain.models.card import MCard
from .domain.dependency.time import get_now_with_located_zone
from .domain.models.config import AppSettings, HashingSettings
from .domain.models.repository_config import RepositoryConfig, SQLiteConfig
from .infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from .infrastructure.content.interpreter import ContentTypeInterpreter
from .application.card_service import CardService

__version__ = "0.2.0"
__all__ = [
    "MCard",
    "get_now_with_located_zone",
    "AppSettings",
    "HashingSettings",
    "RepositoryConfig",
    "SQLiteConfig",
    "SQLiteStore",
    "ContentTypeInterpreter",
    "CardService"
]
