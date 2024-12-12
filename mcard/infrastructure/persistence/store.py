"""
MCardStore singleton class that provides a unified interface for all persistence operations.
This class follows the Singleton pattern to ensure a single instance is shared across the application.
"""

import os
import sqlite3
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from threading import Lock
from contextlib import contextmanager

from mcard.domain.models.domain_config_models import HashingSettings
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError, ConfigurationError
from mcard.infrastructure.persistence.database_engine_config import EngineConfig, EngineType, create_engine_config
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.infrastructure_config_manager import load_config
import asyncio

class MCardStore:
    """
    Singleton class for managing all persistence operations.
    This class provides a unified interface for storing and retrieving cards,
    while abstracting away the specific database implementation details.
    """
    _instance = None
    _lock = Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the store with optional configuration.
        
        Args:
            config: Optional configuration object
        """
        self._config = config or load_config()
        self._facade: Optional[SQLiteStore] = None
        self._hashing_service: Optional[HashingSettings] = None
        self._initialized = False

    async def __aenter__(self):
        """
        Async context manager entry point.
        
        Returns:
            Initialized store instance
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        await self.close()

    async def initialize(self):
        """Initialize the store with current configuration."""
        if not self._config:
            raise ConfigurationError("Store must be configured before initialization")

        # Configure the store if not already configured
        if not self._facade:
            self.configure()

        # Initialize services
        hashing_settings = HashingSettings(algorithm=self._config.hashing['algorithm'])
        self._hashing_service = hashing_settings

        # Initialize the facade with SQLiteConfig
        if isinstance(self._config, EngineConfig):
            store_config = self._config
        else:
            store_config = create_engine_config(
                engine_type=EngineType.SQLITE,
                connection_string=self._config.repository.db_path,
                max_connections=self._config.repository.max_connections,
                timeout=self._config.repository.timeout,
                max_content_size=self._config.max_content_size,
                engine_options={'check_same_thread': False}
            )
        self._facade = SQLiteStore(store_config)

        # Initialize the database connection and schema
        await self._facade.initialize()
        self._initialized = True

    async def close(self):
        """Close the store and release resources."""
        if self._initialized and self._facade:
            await self._facade.close()
            self._initialized = False

    async def reset(self):
        """Reset the store to its initial state."""
        await self.close()
        self._config = load_config()
        self._facade = None
        self._hashing_service = None
        self._initialized = False

    def configure(
        self, 
        engine_type: Optional[EngineType] = None, 
        connection_string: Optional[str] = None,
        max_connections: Optional[int] = None,
        timeout: Optional[float] = None
    ):
        """
        Configure the store with specific parameters.
        
        Args:
            engine_type: Type of database engine
            connection_string: Database connection string
            max_connections: Maximum number of connections
            timeout: Connection timeout
        """
        # Reset configuration
        self._config = load_config()

        # Override configuration if specific parameters are provided
        if engine_type:
            # Create new engine config with provided parameters, falling back to existing values
            engine_config = create_engine_config(
                engine_type=engine_type,
                connection_string=connection_string or self._config.engine_config.connection_string,
                max_connections=max_connections or self._config.engine_config.max_connections,
                timeout=timeout or self._config.engine_config.timeout
            )
            self._config.engine_config = engine_config

    def compute_hash(self, content: bytes) -> str:
        """Compute hash for given content."""
        return run(self._hashing_service.hash_content(content))

    async def save(self, card: MCard) -> None:
        """Save a card to the store."""
        if card is None:
            raise ValueError("Card cannot be None")
        if not self._facade:
            raise StorageError("Store not configured")
        
        if card.hash is None:
            card.hash = self.compute_hash(card.content.encode('utf-8'))
        await self._facade.save_card(card)

    def save_sync(self, card: MCard) -> None:
        """Save a card synchronously."""
        run(self.save(card))

    async def get(self, card_id: str) -> Optional[MCard]:
        """Retrieve a card by its ID."""
        if card_id is None:
            raise ValueError("Card ID cannot be None")
        if not self._facade:
            raise StorageError("Store not configured")
        return await self._facade.get_card(card_id)

    def get_sync(self, card_id: str) -> Optional[MCard]:
        """Retrieve a card synchronously."""
        return run(self.get(card_id))

    async def delete(self, card_id: str) -> None:
        """Delete a card by its ID."""
        if card_id is None:
            raise ValueError("Card ID cannot be None")
        if not self._facade:
            raise StorageError("Store not configured")
        await self._facade.delete_card(card_id)

    def delete_sync(self, card_id: str) -> None:
        """Delete a card synchronously."""
        run(self.delete(card_id))

    async def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List cards with optional pagination."""
        if not self._facade:
            raise StorageError("Store not configured")
        return await self._facade.list_cards(limit=limit, offset=offset)

    def list_sync(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List cards synchronously."""
        return run(self.list(limit=limit, offset=offset))

    async def search(self, query: str) -> List[MCard]:
        """Search for cards based on a query."""
        if query is None:
            raise ValueError("Query cannot be None")
        if not self._facade:
            raise StorageError("Store not configured")
        return await self._facade.search_cards(query)

    def search_sync(self, query: str) -> List[MCard]:
        """Search for cards synchronously."""
        return run(self.search(query))

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards in a batch."""
        if cards is None:
            raise ValueError("Cards cannot be None")
        if not self._facade:
            raise StorageError("Store not configured")
        
        # Compute hashes for cards that don't have them
        for card in cards:
            if card.hash is None:
                card.hash = self.compute_hash(card.content.encode('utf-8'))
        await self._facade.save_many_cards(cards)

    def save_many_sync(self, cards: List[MCard]) -> None:
        """Save multiple cards synchronously."""
        run(self.save_many(cards))

    @property
    def is_configured(self) -> bool:
        """Check if the store is configured."""
        return self._facade is not None

    @property
    def config(self) -> Optional[Dict[str, Any]]:
        """Get the current database configuration."""
        return self._config
