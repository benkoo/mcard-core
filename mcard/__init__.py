"""
MCard Core: A content-addressable data wrapper library.
"""

from .domain.models.card import MCard
from .domain.services.time import get_now_with_located_zone
from .domain.models.config import AppSettings, HashingSettings, DatabaseSettings
from .infrastructure.persistence.sqlite import SQLiteRepository
from .infrastructure.content.interpreter import ContentTypeInterpreter
from .application.card_service import CardService

__version__ = "0.2.0"
__all__ = [
    "MCard",
    "get_now_with_located_zone",
    "AppSettings",
    "HashingSettings",
    "DatabaseSettings",
    "SQLiteRepository",
    "ContentTypeInterpreter",
    "CardService"
]
