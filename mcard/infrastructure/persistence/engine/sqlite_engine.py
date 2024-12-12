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
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig, EngineConfig, EngineType, DatabaseType
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
            logger.debug(f'Initializing SQLite database at {self._config.db_path}')  # Log initialization
            # Ensure the database directory exists
            db_path = Path(self._config.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create the database file if it does not exist
            if not db_path.exists():
                logger.debug(f'Creating database file at {db_path}')  # Log file creation
                open(db_path, 'a').close()  # Create an empty file if it doesn't exist

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
                # Store content as string
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
                    content = row[0].decode() if isinstance(row[0], bytes) else row[0]
                    return MCard(content=content, hash=hash_str, g_time=row[1])
                return None
            finally:
                await cursor.close()

        return await self._execute_with_retry(_get)

    async def get_total_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        hash_search: Optional[str] = None,
        g_time_search: Optional[str] = None,
    ) -> int:
        """Get total count of cards with optional filtering."""
        if not self._initialized:
            await self.initialize()

        async def _count():
            cursor = await self._connection.cursor()
            try:
                query = ['SELECT COUNT(*) FROM card WHERE 1=1']
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
                if hash_search:
                    query.append('AND hash LIKE ?')
                    params.append(f'%{hash_search}%')
                if g_time_search:
                    query.append('AND g_time LIKE ?')
                    params.append(f'%{g_time_search}%')

                await cursor.execute(' '.join(query), params)
                row = await cursor.fetchone()
                return row[0] if row else 0
            finally:
                await cursor.close()

        return await self._execute_with_retry(_count)

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        content: Optional[str] = None,
        hash_search: Optional[str] = None,
        g_time_search: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Tuple[List[MCard], Optional[Dict]]:
        """List cards with optional filtering and pagination.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            content: Optional content filter
            hash_search: Optional hash text search
            g_time_search: Optional g_time text search
            page: Optional page number (1-based)
            page_size: Optional page size
            
        Returns:
            Tuple of (list of cards, pagination info dict)
            Pagination info includes: total, page, page_size, total_pages, has_next, has_previous
        """
        if not self._initialized:
            await self.initialize()

        # Calculate pagination parameters
        if page is not None and page_size is not None:
            if page < 1:
                raise ValidationError("Page number must be >= 1")
            if page_size < 1:
                raise ValidationError("Page size must be >= 1")
            offset = (page - 1) * page_size
            limit = page_size
        else:
            offset = None
            limit = None

        async def _list():
            cursor = await self._connection.cursor()
            try:
                query = ['SELECT hash, content, g_time FROM card WHERE 1=1']
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
                if hash_search:
                    query.append('AND hash LIKE ?')
                    params.append(f'%{hash_search}%')
                if g_time_search:
                    query.append('AND g_time LIKE ?')
                    params.append(f'%{g_time_search}%')

                query.append('ORDER BY g_time DESC')

                if limit is not None:
                    query.append('LIMIT ?')
                    params.append(limit)
                if offset is not None:
                    query.append('OFFSET ?')
                    params.append(offset)

                await cursor.execute(' '.join(query), params)
                rows = await cursor.fetchall()
                cards = [MCard(content=row[1], 
                             hash=row[0], 
                             g_time=row[2]) for row in rows]

                # Get pagination info if needed
                pagination_info = None
                if page is not None and page_size is not None:
                    total = await self.get_total_count(
                        start_time=start_time,
                        end_time=end_time,
                        content=content,
                        hash_search=hash_search,
                        g_time_search=g_time_search,
                    )
                    total_pages = (total + page_size - 1) // page_size
                    pagination_info = {
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }

                return cards, pagination_info
            finally:
                await cursor.close()

        return await self._execute_with_retry(_list)

    async def search(
        self,
        query: str,
        search_hash: bool = True,
        search_content: bool = True,
        search_time: bool = True,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Tuple[List[MCard], Optional[Dict]]:
        """Search cards by text in hash, content, and/or g_time fields.
        
        Args:
            query: Text to search for
            search_hash: Whether to search in hash field
            search_content: Whether to search in content field
            search_time: Whether to search in g_time field
            page: Optional page number (1-based)
            page_size: Optional page size
            
        Returns:
            Tuple of (list of cards, pagination info dict)
        """
        if not any([search_hash, search_content, search_time]):
            raise ValidationError("At least one search field must be enabled")

        if not self._initialized:
            await self.initialize()

        # Calculate pagination parameters
        if page is not None and page_size is not None:
            if page < 1:
                raise ValidationError("Page number must be >= 1")
            if page_size < 1:
                raise ValidationError("Page size must be >= 1")
            offset = (page - 1) * page_size
            limit = page_size
        else:
            offset = None
            limit = None

        async def _search():
            cursor = await self._connection.cursor()
            try:
                query_parts = []
                params = []

                if search_hash:
                    query_parts.append('hash LIKE ?')
                    params.append(f'%{query}%')
                if search_content:
                    query_parts.append('content LIKE ?')
                    params.append(f'%{query}%')
                if search_time:
                    query_parts.append('g_time LIKE ?')
                    params.append(f'%{query}%')

                sql = f'''
                    SELECT hash, content, g_time 
                    FROM card 
                    WHERE {' OR '.join(query_parts)}
                    ORDER BY g_time DESC
                '''

                if limit is not None:
                    sql += ' LIMIT ?'
                    params.append(limit)
                if offset is not None:
                    sql += ' OFFSET ?'
                    params.append(offset)

                await cursor.execute(sql, params)
                rows = await cursor.fetchall()
                cards = [MCard(content=row[1], 
                             hash=row[0], 
                             g_time=row[2]) for row in rows]

                # Get pagination info if needed
                pagination_info = None
                if page is not None and page_size is not None:
                    # Count total matching rows
                    count_sql = f'''
                        SELECT COUNT(*) 
                        FROM card 
                        WHERE {' OR '.join(query_parts)}
                    '''
                    await cursor.execute(count_sql, params[:-2] if limit is not None else params)
                    total = (await cursor.fetchone())[0]
                    
                    total_pages = (total + page_size - 1) // page_size
                    pagination_info = {
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }

                return cards, pagination_info
            finally:
                await cursor.close()

        return await self._execute_with_retry(_search)

    async def save(self, card: MCard) -> None:
        """Save a card to the database."""
        if not self._initialized:
            await self.initialize()

        if not card.content:
            raise ValidationError("Content cannot be empty")

        if len(str(card.content)) > self.max_content_size:
            raise ValidationError(f"Content size exceeds maximum allowed size of {self.max_content_size} bytes")

        async def _save():
            logger.debug(f'Attempting to save card with hash: {card.hash} to database')
            async with self._connection.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO card (hash, content, g_time) VALUES (?, ?, ?)",
                    (card.hash, card.content, card.g_time)
                )
                await self._connection.commit()
                logger.debug(f'Successfully saved card with hash: {card.hash} to database')

        try:
            await self._execute_with_retry(_save)
        except Exception as e:
            logger.error(f'Failed to save card with hash: {card.hash}, error: {str(e)}')
            raise StorageError(f"Failed to save card: {str(e)}")

    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        if not self._initialized:
            await self.initialize()

        async def _remove():
            cursor = await self._connection.cursor()
            try:
                # First check if the card exists
                await cursor.execute('SELECT 1 FROM card WHERE hash = ?', (hash_str,))
                if not await cursor.fetchone():
                    return  # Card doesn't exist, nothing to delete
                    
                # Delete the card
                await cursor.execute('DELETE FROM card WHERE hash = ?', (hash_str,))
                await self._connection.commit()
                
                # Verify the deletion
                await cursor.execute('SELECT 1 FROM card WHERE hash = ?', (hash_str,))
                if await cursor.fetchone():
                    raise StorageError(f"Failed to delete card with hash {hash_str}")
            finally:
                await cursor.close()

        await self._execute_with_retry(_remove)

    async def delete_all(self) -> None:
        """Delete all cards from the store."""
        if not self._initialized:
            await self.initialize()

        async def _delete_all():
            cursor = await self._connection.cursor()
            try:
                await cursor.execute('DELETE FROM card')
                await self._connection.commit()
            finally:
                await cursor.close()

        await self._execute_with_retry(_delete_all)
