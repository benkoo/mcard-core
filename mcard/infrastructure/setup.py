"""
MCard Setup Configuration

This module provides a reusable setup and configuration functionality for the MCard storage system.
It can be used by any application that needs to interact with MCard storage.
"""

import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from mcard import MCard, ContentTypeInterpreter
from mcard.infrastructure.persistence.async_persistence_wrapper import AsyncPersistenceWrapper
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.domain.models.exceptions import StorageError


class MCardSetup:
    """Setup class for MCard storage system."""
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        max_connections: int = 5,
        timeout: float = 5.0,
        max_content_size: int = 10 * 1024 * 1024,  # 10MB
        engine_type: EngineType = EngineType.SQLITE,
        config_overrides: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MCard Storage with configuration options.
        
        Args:
            db_path (Optional[str]): Path to database. Defaults to in-memory database if not provided.
            max_connections (int): Maximum number of database connections. Defaults to 5.
            timeout (float): Database operation timeout in seconds. Defaults to 5.0.
            max_content_size (int): Maximum content size in bytes. Defaults to 10MB.
            engine_type (EngineType): Type of database engine to use. Defaults to SQLite.
            config_overrides (Optional[Dict[str, Any]]): Additional configuration options to override defaults.
        """
        # Set up engine configuration
        if engine_type == EngineType.SQLITE:
            engine_config = SQLiteConfig(
                db_path=db_path or ":memory:",
                max_connections=max_connections,
                timeout=timeout,
                check_same_thread=False,
                max_content_size=max_content_size
            )
            
            # Apply any overrides
            if config_overrides:
                for key, value in config_overrides.items():
                    if hasattr(engine_config, key):
                        setattr(engine_config, key, value)
        else:
            raise ValueError(f"Unsupported engine type: {engine_type}")
            
        self.storage = AsyncPersistenceWrapper(engine_config)
        self.content_interpreter = ContentTypeInterpreter()
        
    async def initialize(self):
        """Initialize the storage system."""
        await self.storage.initialize()
        
    async def cleanup(self):
        """Clean up resources."""
        await self.storage.close()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
