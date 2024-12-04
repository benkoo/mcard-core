"""SQLite store implementation."""
import os
import sqlite3
import threading
import logging
import asyncio
from typing import List, Optional, Union, Dict, Tuple
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import ValidationError, StorageError
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType, DatabaseType
from mcard.infrastructure.persistence.schema import SchemaManager
from mcard.infrastructure.persistence.engine.base_engine import BaseStore

logger = logging.getLogger(__name__)


class SQLiteStore(BaseStore):
    """SQLite store implementation."""

    def __init__(self, config: Union[str, SQLiteConfig]):
        """Initialize SQLite store with config."""
        # Convert string to SQLiteConfig if needed
        if isinstance(config, str):
            config = SQLiteConfig(db_path=config)

        self._config = config
        self._connection: Optional[aiosqlite.Connection] = None
        self._initialized = False
        self.max_content_size = config.max_content_size
        self._local = threading.local()
        self._schema_manager = SchemaManager()
        self._busy_timeout = config.timeout or 5000  # Default 5 second timeout
        self._max_retries = 3
        self._retry_delay = 0.1  # 100ms

    async def initialize(self):
        """Initialize the database connection."""
        if not self._initialized:
            # Ensure the database directory exists
            db_path = Path(self._config.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Open connection
            self._connection = await aiosqlite.connect(
                self._config.db_path,
                timeout=self._config.timeout
            )
            
            # Configure connection
            await self._connection.execute('PRAGMA journal_mode=WAL')
            await self._connection.execute('PRAGMA synchronous=NORMAL')
            await self._connection.execute('PRAGMA foreign_keys=ON')
            await self._connection.execute(f'PRAGMA busy_timeout={self._busy_timeout}')
            
            # Initialize schema using SchemaManager
            await self._schema_manager.initialize_schema(EngineType.SQLITE, self._connection)
            
            await self._connection.commit()
            self._initialized = True

    async def close(self):
        """Close the database connection."""
        if self._initialized and self._connection:
            await self._connection.close()
            self._initialized = False

    async def _execute_with_retry(self, operation, *args):
        """Execute a database operation with retry logic."""
        for attempt in range(self._max_retries):
            try:
                return await operation(*args)
            except sqlite3.OperationalError as e:
                if attempt == self._max_retries - 1:
                    raise StorageError(f"Database operation failed after {self._max_retries} attempts: {e}")
                await asyncio.sleep(self._retry_delay * (attempt + 1))

    async def create(self, content: str) -> MCard:
        """Create a new card with the given content."""
        if not self._initialized:
            await self.initialize()

        if not content:
            raise ValidationError("Content cannot be empty")

        if len(content) > self.max_content_size:
            raise ValidationError(f"Content size exceeds maximum allowed size of {self.max_content_size} bytes")

        async def _create():
            cursor = await self._connection.cursor()
            try:
                now = datetime.now(timezone.utc).isoformat()
                card = MCard(content=content, g_time=now)
                await cursor.execute(
                    'INSERT INTO card (hash, content, g_time) VALUES (?, ?, ?)',
                    (card.hash, content, now)
                )
                await self._connection.commit()
                return card
            finally:
                await cursor.close()

        return await self._execute_with_retry(_create)

    async def create_many(self, contents: List[str]) -> List[MCard]:
        """Create multiple cards with the given contents."""
        if not self._initialized:
            await self.initialize()

        cards = []
        async def _create_many():
            cursor = await self._connection.cursor()
            try:
                now = datetime.now(timezone.utc).isoformat()
                for content in contents:
                    if not content:
                        raise ValidationError("Content cannot be empty")
                    if len(content) > self.max_content_size:
                        raise ValidationError(f"Content size exceeds maximum allowed size of {self.max_content_size} bytes")
                    
                    card = MCard(content=content, g_time=now)
                    await cursor.execute(
                        'INSERT INTO card (hash, content, g_time) VALUES (?, ?, ?)',
                        (card.hash, content, now)
                    )
                    cards.append(card)
                await self._connection.commit()
                return cards
            finally:
                await cursor.close()

        return await self._execute_with_retry(_create_many)

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Get a card by its hash."""
        if not self._initialized:
            await self.initialize()

        async def _get():
            cursor = await self._connection.cursor()
            try:
                await cursor.execute('SELECT content, g_time FROM card WHERE hash = ?', (hash_str,))
                row = await cursor.fetchone()
                if row:
                    return MCard(content=row[0], hash=hash_str, g_time=row[1])
                return None
            finally:
                await cursor.close()

        return await self._execute_with_retry(_get)

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[MCard]:
        """List cards with optional filtering and pagination."""
        if not self._initialized:
            await self.initialize()

        async def _list():
            cursor = await self._connection.cursor()
            try:
                query = ['SELECT content, g_time FROM card WHERE 1=1']
                params = []

                if start_time:
                    query.append('AND g_time >= ?')
                    params.append(start_time.isoformat())
                if end_time:
                    query.append('AND g_time <= ?')
                    params.append(end_time.isoformat())
                if content:
                    query.append('AND content LIKE ?')
                    params.append(f'%{content}%')

                query.append('ORDER BY g_time DESC')

                if limit is not None:
                    query.append('LIMIT ?')
                    params.append(limit)
                if offset is not None:
                    query.append('OFFSET ?')
                    params.append(offset)

                await cursor.execute(' '.join(query), params)
                rows = await cursor.fetchall()
                return [MCard(content=row[0], hash=None, g_time=row[1]) for row in rows]
            finally:
                await cursor.close()

        return await self._execute_with_retry(_list)

    async def save(self, card: MCard) -> None:
        """Save a card to the store."""
        if not self._initialized:
            await self.initialize()

        if not card.content:
            raise ValidationError("Content cannot be empty")

        if len(str(card.content)) > self.max_content_size:
            raise ValidationError(f"Content size exceeds maximum allowed size of {self.max_content_size} bytes")

        async def _save():
            cursor = await self._connection.cursor()
            try:
                # Check if hash already exists
                await cursor.execute('SELECT 1 FROM card WHERE hash = ?', (card.hash,))
                if await cursor.fetchone():
                    raise StorageError(f"Card with hash {card.hash} already exists")
                    
                # Insert new card
                now = datetime.now(timezone.utc).isoformat()
                try:
                    await cursor.execute(
                        'INSERT INTO card (content, hash, g_time) VALUES (?, ?, ?)',
                        (card.content, card.hash, now)
                    )
                    await self._connection.commit()
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        raise StorageError(f"Card with hash {card.hash} already exists")
                    raise StorageError(f"Failed to save card: {str(e)}")
            finally:
                await cursor.close()

        await self._execute_with_retry(_save)

    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        if not self._initialized:
            await self.initialize()

        async def _remove():
            cursor = await self._connection.cursor()
            try:
                await cursor.execute('DELETE FROM card WHERE hash = ?', (hash_str,))
                await self._connection.commit()
            finally:
                await cursor.close()

        await self._execute_with_retry(_remove)
