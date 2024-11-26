"""
SQLite implementation of the card repository.
"""
import sqlite3
import aiosqlite
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from ...domain.models.card import MCard
from ...domain.models.protocols import CardRepository
from ...domain.models.exceptions import StorageError, ValidationError
from ..content.interpreter import ContentTypeInterpreter

class SQLiteCardRepository(CardRepository):
    """SQLite implementation of card repository."""

    def __init__(self, db_path: str, pool_size: int = 5, max_content_size: int = 100 * 1024 * 1024):
        """Initialize repository with database path and connection pool.
        
        Args:
            db_path: Path to SQLite database
            pool_size: Maximum number of connections in the pool
            max_content_size: Maximum content size in bytes (default 100MB)
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_content_size = max_content_size
        self._connection_pool: List[aiosqlite.Connection] = []
        self._pool_lock = asyncio.Lock()
        self._transaction_connections: Dict[int, aiosqlite.Connection] = {}
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cards (
                        hash TEXT PRIMARY KEY,
                        content BLOB NOT NULL,
                        g_time TIMESTAMP NOT NULL
                    )
                """)
                # Add index for timestamp-based queries
                conn.execute("CREATE INDEX IF NOT EXISTS idx_g_time ON cards(g_time)")
                conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to initialize database: {str(e)}")

    @asynccontextmanager
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a connection from the pool."""
        task_id = id(asyncio.current_task())
        if task_id in self._transaction_connections:
            yield self._transaction_connections[task_id]
            return

        async with self._pool_lock:
            if not self._connection_pool:
                if len(self._connection_pool) < self.pool_size:
                    conn = await aiosqlite.connect(self.db_path)
                    await conn.execute("PRAGMA journal_mode=WAL")
                    await conn.execute("PRAGMA synchronous=NORMAL")
                    await conn.execute("PRAGMA temp_store=MEMORY")
                else:
                    raise StorageError("Connection pool exhausted")
            else:
                conn = self._connection_pool.pop()

        try:
            yield conn
        finally:
            if not self._transaction_connections.get(task_id):
                async with self._pool_lock:
                    self._connection_pool.append(conn)

    def _validate_content_size(self, content: bytes) -> None:
        """Validate content size."""
        if len(content) > self.max_content_size:
            raise ValidationError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")

    async def save(self, card: MCard) -> None:
        """Save a card to the database."""
        content = card.content
        if isinstance(content, str):
            content = content.encode('utf-8')
        elif not isinstance(content, (bytes, bytearray)):
            content = str(content).encode('utf-8')

        self._validate_content_size(content)
        
        try:
            async with self._get_connection() as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO cards
                    (hash, content, g_time)
                    VALUES (?, ?, ?)
                    """,
                    (
                        card.hash,
                        content,
                        card.g_time.astimezone(timezone.utc)
                    )
                )
                await db.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save card: {str(e)}")

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards to the database."""
        if not cards:
            return

        try:
            async with self._get_connection() as db:
                values = []
                for card in cards:
                    content = card.content
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    elif not isinstance(content, (bytes, bytearray)):
                        content = str(content).encode('utf-8')
                    
                    self._validate_content_size(content)
                    values.append((
                        card.hash,
                        content,
                        card.g_time.astimezone(timezone.utc)
                    ))

                await db.executemany(
                    """
                    INSERT OR REPLACE INTO cards
                    (hash, content, g_time)
                    VALUES (?, ?, ?)
                    """,
                    values
                )
                await db.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save cards: {str(e)}")

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        try:
            async with self._get_connection() as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM cards WHERE hash = ?",
                    (hash_str,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row is None:
                        return None
                    
                    content = row['content']
                    if not ContentTypeInterpreter.is_binary_content(content):
                        content = content.decode('utf-8')
                    
                    return MCard(
                        content=content,
                        hash=row['hash'],
                        g_time=row['g_time'].replace(tzinfo=timezone.utc).astimezone()
                    )
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve card: {str(e)}")

    async def get_many(self, hash_strs: List[str]) -> List[MCard]:
        """Retrieve multiple cards by their hashes."""
        if not hash_strs:
            return []

        try:
            async with self._get_connection() as db:
                db.row_factory = aiosqlite.Row
                placeholders = ','.join('?' * len(hash_strs))
                async with db.execute(
                    f"SELECT * FROM cards WHERE hash IN ({placeholders})",
                    hash_strs
                ) as cursor:
                    cards = []
                    async for row in cursor:
                        content = row['content']
                        if not ContentTypeInterpreter.is_binary_content(content):
                            content = content.decode('utf-8')
                        
                        cards.append(MCard(
                            content=content,
                            hash=row['hash'],
                            g_time=row['g_time'].replace(tzinfo=timezone.utc).astimezone()
                        ))
                    return cards
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Retrieve all cards with pagination support."""
        try:
            async with self._get_connection() as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM cards ORDER BY g_time DESC"
                params = []
                
                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                    if offset is not None:
                        query += " OFFSET ?"
                        params.append(offset)

                cards = []
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        content = row['content']
                        if not ContentTypeInterpreter.is_binary_content(content):
                            content = content.decode('utf-8')
                        
                        cards.append(MCard(
                            content=content,
                            hash=row['hash'],
                            g_time=row['g_time'].replace(tzinfo=timezone.utc).astimezone()
                        ))
                return cards
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    async def delete(self, hash_str: str) -> None:
        """Delete a card by its hash."""
        try:
            async with self._get_connection() as db:
                await db.execute(
                    "DELETE FROM cards WHERE hash = ?",
                    (hash_str,)
                )
                await db.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete card: {str(e)}")

    async def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards by their hashes."""
        if not hash_strs:
            return

        try:
            async with self._get_connection() as db:
                placeholders = ','.join('?' * len(hash_strs))
                await db.execute(
                    f"DELETE FROM cards WHERE hash IN ({placeholders})",
                    hash_strs
                )
                await db.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete cards: {str(e)}")

    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        task_id = id(asyncio.current_task())
        if task_id in self._transaction_connections:
            raise StorageError("Transaction already in progress")

        conn = await aiosqlite.connect(self.db_path)
        await conn.execute("BEGIN")
        self._transaction_connections[task_id] = conn

    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        task_id = id(asyncio.current_task())
        if task_id not in self._transaction_connections:
            raise StorageError("No transaction in progress")

        try:
            conn = self._transaction_connections[task_id]
            await conn.commit()
        finally:
            await self._cleanup_transaction(task_id)

    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        task_id = id(asyncio.current_task())
        if task_id not in self._transaction_connections:
            raise StorageError("No transaction in progress")

        try:
            conn = self._transaction_connections[task_id]
            await conn.rollback()
        finally:
            await self._cleanup_transaction(task_id)

    async def _cleanup_transaction(self, task_id: int) -> None:
        """Clean up transaction resources."""
        if task_id in self._transaction_connections:
            conn = self._transaction_connections[task_id]
            await conn.close()
            del self._transaction_connections[task_id]

    async def close(self) -> None:
        """Close all connections."""
        async with self._pool_lock:
            for conn in self._connection_pool:
                await conn.close()
            self._connection_pool.clear()

        for task_id in list(self._transaction_connections.keys()):
            await self._cleanup_transaction(task_id)
