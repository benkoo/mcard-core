"""SQLite store implementation."""
import os
import sqlite3
import threading
import logging
import asyncio
from typing import List, Optional, Union, Dict, Tuple
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import ValidationError, StorageError
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType, DatabaseType
from mcard.infrastructure.persistence.schema import SchemaManager
from mcard.domain.models.protocols import CardStore
import aiosqlite
from pathlib import Path

logger = logging.getLogger(__name__)

class SQLiteStore(CardStore):
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
            
            # Create table if not exists
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    hash TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    g_time TEXT NOT NULL
                )
            """)
            await self._connection.commit()
            self._initialized = True

    async def close(self):
        """Close the database connection."""
        if self._initialized and self._connection:
            await self._connection.close()
            self._initialized = False

    async def reset(self):
        """Reset the store to its initial state."""
        await self.close()
        self._connection = None
        self._initialized = False

    async def _execute_with_retry(self, operation, *args):
        """Execute a database operation with retry logic."""
        for attempt in range(self._max_retries):
            try:
                return await operation(*args)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    continue
                raise StorageError(f"Database operation failed: {str(e)}")
            except Exception as e:
                raise StorageError(f"Database operation failed: {str(e)}")

    async def get_all(self, content: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Get all cards from the database with optional filtering and pagination."""
        await self.initialize()
        query = 'SELECT hash, content, g_time FROM cards'
        params = []
        
        if content is not None:
            query += ' WHERE content LIKE ?'
            params.append(f'%{content}%')
            
        query += ' ORDER BY g_time DESC'
            
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
            
        if offset is not None:
            query += ' OFFSET ?'
            params.append(offset)
            
        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()
        
        cards = []
        for row in rows:
            hash_str, content, g_time = row
            restored_content = self._restore_content_from_storage(content)
            cards.append(MCard(content=restored_content, hash=hash_str, g_time=g_time))
        return cards

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Get a card by its hash."""
        await self.initialize()
        
        async def _get():
            cursor = await self._connection.execute(
                "SELECT content, g_time FROM cards WHERE hash = ?",
                (hash_str,)
            )
            row = await cursor.fetchone()
            if row:
                content, g_time = row
                restored_content = self._restore_content_from_storage(content)
                return MCard(content=restored_content, hash=hash_str, g_time=g_time)
            return None

        return await self._execute_with_retry(_get)

    async def get_many(self, hashes: List[str]) -> List[MCard]:
        """Get multiple cards by their hashes."""
        await self.initialize()
        if not hashes:
            return []

        placeholders = ','.join(['?' for _ in hashes])
        query = f'SELECT hash, content, g_time FROM cards WHERE hash IN ({placeholders})'
        cursor = await self._connection.execute(query, hashes)
        rows = await cursor.fetchall()

        cards = []
        for row in rows:
            hash_str, content, g_time = row
            restored_content = self._restore_content_from_storage(content)
            cards.append(MCard(content=restored_content, hash=hash_str, g_time=g_time))
        return cards

    async def save(self, card: MCard) -> None:
        """Save a card to the database."""
        await self.initialize()
        
        content_size = len(card.content.encode()) if isinstance(card.content, str) else len(card.content)
        if content_size > self.max_content_size:
            raise StorageError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")

        content_bytes = self._prepare_content_for_storage(card.content)
        formatted_time = self._format_timestamp(card.g_time)
        
        async def _save():
            try:
                await self._connection.execute(
                    'INSERT INTO cards (hash, content, g_time) VALUES (?, ?, ?)',
                    (card.hash, content_bytes, formatted_time)
                )
                await self._connection.commit()
            except sqlite3.IntegrityError as e:
                raise StorageError(f"Card with hash {card.hash} already exists") from e
            except sqlite3.Error as e:
                raise StorageError(f"Failed to save card: {str(e)}") from e

        await self._execute_with_retry(_save)

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards to the database."""
        await self.initialize()
        
        for card in cards:
            await self.save(card)

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        """List cards from the store with optional time range and pagination."""
        await self.initialize()
        query = 'SELECT hash, content, g_time FROM cards WHERE 1=1'
        params = []
        
        if start_time:
            query += ' AND g_time >= ?'
            params.append(start_time.isoformat())
        
        if end_time:
            query += ' AND g_time <= ?'
            params.append(end_time.isoformat())
        
        query += ' ORDER BY g_time DESC'
        
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
        
        if offset is not None:
            query += ' OFFSET ?'
            params.append(offset)
        
        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()
        
        return [
            MCard(content=self._restore_content_from_storage(content), hash=hash_str, g_time=g_time)
            for hash_str, content, g_time in rows
        ]

    async def get_by_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        """Retrieve cards within a time range."""
        return await self.list(start_time, end_time, limit, offset)

    async def get_before_time(
        self,
        time: datetime,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        """Retrieve cards created before the specified time."""
        return await self.list(end_time=time, limit=limit, offset=offset)

    async def get_after_time(
        self,
        time: datetime,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MCard]:
        """Retrieve cards created after the specified time."""
        return await self.list(start_time=time, limit=limit, offset=offset)

    async def delete(self, hash_str: str) -> None:
        """Delete a card from the store by its hash."""
        await self.initialize()
        
        async def _delete():
            try:
                await self._connection.execute('DELETE FROM cards WHERE hash = ?', (hash_str,))
                await self._connection.commit()
            except sqlite3.Error as e:
                raise StorageError(f"Failed to delete card: {str(e)}") from e

        await self._execute_with_retry(_delete)

    async def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards from the store by their hashes."""
        await self.initialize()
        
        async def _delete_many():
            try:
                placeholders = ','.join(['?' for _ in hash_strs])
                await self._connection.execute(f'DELETE FROM cards WHERE hash IN ({placeholders})', hash_strs)
                await self._connection.commit()
            except sqlite3.Error as e:
                raise StorageError(f"Failed to delete cards: {str(e)}") from e

        await self._execute_with_retry(_delete_many)

    async def delete_before_time(self, time: datetime) -> int:
        """Delete all cards created before the specified time."""
        await self.initialize()
        
        async def _delete_before_time():
            try:
                await self._connection.execute('DELETE FROM cards WHERE g_time < ?', (time.isoformat(),))
                await self._connection.commit()
                return await self._connection.total_changes
            except sqlite3.Error as e:
                raise StorageError(f"Failed to delete cards before time: {str(e)}") from e

        return await self._execute_with_retry(_delete_before_time)

    async def begin_transaction(self) -> None:
        """Begin a store transaction."""
        await self._connection.execute('BEGIN TRANSACTION')

    async def commit_transaction(self) -> None:
        """Commit the current store transaction."""
        await self._connection.commit()

    async def rollback_transaction(self) -> None:
        """Rollback the current store transaction."""
        await self._connection.rollback()

    def _prepare_content_for_storage(self, content: Union[str, bytes]) -> bytes:
        """Prepare content for storage by converting to bytes if needed."""
        if isinstance(content, str):
            return content.encode('utf-8')
        return content

    def _restore_content_from_storage(self, content: bytes) -> Union[str, bytes]:
        """Restore content from storage."""
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content

    def _format_timestamp(self, timestamp: Union[str, datetime]) -> str:
        """Format timestamp as ISO 8601 string with timezone."""
        if isinstance(timestamp, str):
            # Validate that the string is a proper ISO format
            try:
                datetime.fromisoformat(timestamp)
                return timestamp
            except ValueError as e:
                raise ValidationError(f"Invalid timestamp format. Expected ISO 8601 format: {str(e)}")
        elif isinstance(timestamp, datetime):
            # Ensure timezone is set
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return timestamp.isoformat()
        else:
            raise ValidationError(f"Invalid timestamp type: {type(timestamp)}")
