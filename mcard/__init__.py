"""
MCard Core: A content-addressable data wrapper library.
"""

from .domain.models.card import MCard
from .domain.dependency.time import get_now_with_located_zone
from .domain.models.config import AppSettings, HashingSettings
from .domain.models.repository_config import RepositoryConfig, SQLiteConfig
from .domain.dependency.interpreter import ContentTypeInterpreter
from .application.card_service import CardService
from .domain.services.hashing import DefaultHashingService, get_hashing_service, set_hashing_service
from .infrastructure.persistence.repositories import SQLiteCardRepo

__version__ = "0.2.0"
__all__ = [
    "MCard",
    "get_now_with_located_zone",
    "AppSettings",
    "HashingSettings",
    "RepositoryConfig",
    "SQLiteConfig",
    "ContentTypeInterpreter",
    "CardService",
    "DefaultHashingService",
    "get_hashing_service",
    "set_hashing_service",
    "SQLiteCardRepo",
]
