"""SQLite store implementation."""
import os
import sqlite3
import threading
import logging
from typing import List, Optional, Union, Dict, Tuple
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import ValidationError, StorageError
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType, DatabaseType
from mcard.infrastructure.persistence.schema import SchemaManager
from mcard.domain.models.protocols import CardStore
import aiosqlite

logger = logging.getLogger(__name__)

class SQLiteStore(CardStore):
    """SQLite store implementation."""

    def __init__(self, config: Union[str, SQLiteConfig]):
        """Initialize SQLite store with config."""
        # Convert string to SQLiteConfig if needed
        if isinstance(config, str):
            config = SQLiteConfig(db_path=config)

        self.config = config
        self.db_path = config.db_path
        self.max_content_size = config.max_content_size
        self._local = threading.local()
        self._schema_manager = SchemaManager()
        
        # Schema will be initialized when needed
        self._initialized = False

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            try:
                # Create directory if needed
                if self.db_path != ":memory:":
                    directory = os.path.dirname(os.path.abspath(self.db_path))
                    if directory:
                        os.makedirs(directory, exist_ok=True)

                # Create new connection for this thread
                self._local.connection = sqlite3.connect(
                    self.db_path,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
                )
                cursor = self._local.connection.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA busy_timeout=5000')
                cursor.execute('PRAGMA synchronous=FULL')
                cursor.execute('PRAGMA foreign_keys=ON')
            except (OSError, sqlite3.Error) as e:
                raise StorageError(f"Failed to create or connect to database: {str(e)}")

        return self._local.connection

    async def initialize(self) -> None:
        """Initialize the database and create schema if needed."""
        if not self.db_path:
            raise StorageError("Database path not set")

        logger.debug(f"Initializing SQLite database at {self.db_path}")

        # Ensure the directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.debug(f"Created directory {db_dir}")

        try:
            # Let SQLite create the database file
            async with aiosqlite.connect(self.db_path) as db:
                logger.debug("Connected to database")
                await db.execute("PRAGMA foreign_keys = ON")
                
                # Create tables
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS cards (
                        hash TEXT PRIMARY KEY,
                        content BLOB NOT NULL,
                        g_time TEXT NOT NULL
                    )
                ''')
                
                # Create indices
                await db.execute('CREATE INDEX IF NOT EXISTS idx_cards_g_time ON cards(g_time)')
                
                # Add a dummy row and delete it to ensure the schema is written
                await db.execute(
                    "INSERT OR IGNORE INTO cards (hash, content, g_time) VALUES (?, ?, datetime('now'))",
                    ('init', b'init')
                )
                await db.execute("DELETE FROM cards WHERE hash = 'init'")
                
                # Initialize any additional schema components
                if self._schema_manager:
                    await self._schema_manager.initialize_schema(EngineType.SQLITE, db)
                
                await db.commit()
                logger.debug("Completed database initialization")

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise StorageError(f"Failed to initialize database: {str(e)}")

        logger.info(f"Successfully initialized SQLite database at {self.db_path}")

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

    async def get_all(self, content: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Get all cards from the database with optional filtering and pagination."""
        await self.initialize()
        conn = self._get_connection()
        cursor = conn.cursor()
        
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
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        cards = []
        for row in rows:
            hash_str, content, g_time = row
            restored_content = self._restore_content_from_storage(content)
            cards.append(MCard(content=restored_content, hash=hash_str, g_time=g_time))
        return cards

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Get a card by its hash."""
        await self.initialize()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT content, g_time FROM cards WHERE hash = ?', (hash_str,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        content, g_time = row
        restored_content = self._restore_content_from_storage(content)
        return MCard(content=restored_content, hash=hash_str, g_time=g_time)

    async def get_many(self, hashes: List[str]) -> List[MCard]:
        """Get multiple cards by their hashes."""
        await self.initialize()
        if not hashes:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()
        placeholders = ','.join(['?' for _ in hashes])
        query = f'SELECT hash, content, g_time FROM cards WHERE hash IN ({placeholders})'
        cursor.execute(query, hashes)
        rows = cursor.fetchall()

        cards = []
        for row in rows:
            hash_str, content, g_time = row
            restored_content = self._restore_content_from_storage(content)
            cards.append(MCard(content=restored_content, hash=hash_str, g_time=g_time))
        return cards

    async def save(self, card: MCard) -> None:
        """Write a card to the database."""
        await self.initialize()
        content_size = len(card.content.encode()) if isinstance(card.content, str) else len(card.content)
        if content_size > self.max_content_size:
            raise StorageError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")

        content_bytes = self._prepare_content_for_storage(card.content)
        formatted_time = self._format_timestamp(card.g_time)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO cards (hash, content, g_time) VALUES (?, ?, ?)',
                (card.hash, content_bytes, formatted_time)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise StorageError(f"Failed to save card: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise StorageError(f"Failed to save card: {str(e)}")

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards."""
        await self.initialize()
        if not cards:
            return

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            for card in cards:
                content_size = len(card.content.encode()) if isinstance(card.content, str) else len(card.content)
                if content_size > self.max_content_size:
                    raise StorageError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")
                content_bytes = self._prepare_content_for_storage(card.content)
                formatted_time = self._format_timestamp(card.g_time)
                cursor.execute(
                    'INSERT INTO cards (hash, content, g_time) VALUES (?, ?, ?)',
                    (card.hash, content_bytes, formatted_time)
                )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise StorageError(f"Failed to save cards: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise StorageError(f"Failed to save cards: {str(e)}")

    async def delete(self, hash_str: str) -> None:
        """Delete a card by hash."""
        await self.initialize()
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM cards WHERE hash = ?', (hash_str,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError(f"Failed to delete card: {str(e)}")

    async def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
