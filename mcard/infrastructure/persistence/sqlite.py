"""
SQLite implementation of the card repository.
"""
import sqlite3
import aiosqlite
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional, Dict
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError, ValidationError
from mcard.infrastructure.content.interpreter import ContentTypeInterpreter

class SQLiteCardRepository:
    """SQLite implementation of card repository."""

    def __init__(self, db_path: str, pool_size: int = 5, max_content_size: int = 100 * 1024 * 1024):
        """Initialize repository with database path and connection pool."""
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_content_size = max_content_size
        self._connection_pool: List[aiosqlite.Connection] = []
        self._pool_lock = asyncio.Lock()
        self._transaction_connections: Dict[int, aiosqlite.Connection] = {}
        self._transaction_levels: Dict[int, int] = {}  # Track nesting level
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cards (
                        hash TEXT PRIMARY KEY,
                        content BLOB,
                        g_time TIMESTAMP
                    )
                """)
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
            if len(self._connection_pool) < self.pool_size:
                conn = await aiosqlite.connect(self.db_path)
            elif not self._connection_pool:
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
        
        self._validate_content_size(content)
        
        try:
            conn = self._transaction_connections.get(id(asyncio.current_task()))
            if conn:
                # Use transaction connection if in transaction
                await conn.execute(
                    "INSERT OR REPLACE INTO cards (hash, content, g_time) VALUES (?, ?, ?)",
                    (card.hash, sqlite3.Binary(content), card.g_time.astimezone(timezone.utc).isoformat())
                )
            else:
                # Use connection pool if not in transaction
                async with self._get_connection() as db:
                    await db.execute(
                        "INSERT OR REPLACE INTO cards (hash, content, g_time) VALUES (?, ?, ?)",
                        (card.hash, sqlite3.Binary(content), card.g_time.astimezone(timezone.utc).isoformat())
                    )
                    await db.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save card: {str(e)}")

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        if not isinstance(hash_str, str):
            raise StorageError("Hash must be a string")
            
        try:
            conn = self._transaction_connections.get(id(asyncio.current_task()))
            if conn:
                # Use transaction connection if in transaction
                conn.row_factory = aiosqlite.Row
                async with conn.execute(
                    "SELECT * FROM cards WHERE hash = ?",
                    (hash_str,)
                ) as cursor:
                    row = await cursor.fetchone()
            else:
                # Use connection pool if not in transaction
                async with self._get_connection() as db:
                    db.row_factory = aiosqlite.Row
                    async with db.execute(
                        "SELECT * FROM cards WHERE hash = ?",
                        (hash_str,)
                    ) as cursor:
                        row = await cursor.fetchone()
            
            if row is None:
                return None
            
            content = bytes(row['content'])
            # Attempt to decode as UTF-8 if it looks like text
            if not any(b for b in content if b < 32 and b not in (9, 10, 13)):  # Not control chars except tab, newline, carriage return
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    pass  # Keep as bytes if we can't decode
            
            # Parse timestamp and ensure UTC
            g_time = datetime.fromisoformat(row['g_time'])
            if g_time.tzinfo is None:
                g_time = g_time.replace(tzinfo=timezone.utc)
            else:
                g_time = g_time.astimezone(timezone.utc)
            
            return MCard(
                content=content,
                hash=row['hash'],
                g_time=g_time
            )
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve card: {str(e)}")

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards to the database."""
        if not cards:
            return

        if not all(isinstance(card, MCard) for card in cards):
            raise StorageError("All items must be MCard instances")

        try:
            values = []
            for card in cards:
                content = card.content
                if isinstance(content, str):
                    content = content.encode('utf-8')
                elif not isinstance(content, bytes):
                    raise StorageError(f"Invalid content type: {type(content)}")
                
                self._validate_content_size(content)
                values.append((
                    card.hash,
                    sqlite3.Binary(content),
                    card.g_time.astimezone(timezone.utc).isoformat()
                ))

            conn = self._transaction_connections.get(id(asyncio.current_task()))
            if conn:
                # Use transaction connection if in transaction
                await conn.executemany(
                    "INSERT OR REPLACE INTO cards (hash, content, g_time) VALUES (?, ?, ?)",
                    values
                )
            else:
                # Use connection pool if not in transaction
                async with self._get_connection() as db:
                    await db.executemany(
                        "INSERT OR REPLACE INTO cards (hash, content, g_time) VALUES (?, ?, ?)",
                        values
                    )
                    await db.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save cards: {str(e)}")

    async def get_many(self, hash_strs: List[str]) -> List[MCard]:
        """Retrieve multiple cards by their hashes."""
        if not hash_strs:
            return []

        if not all(isinstance(h, str) for h in hash_strs):
            raise StorageError("All hashes must be strings")

        try:
            async with self._get_connection() as db:
                db.row_factory = aiosqlite.Row
                placeholders = ','.join('?' * len(hash_strs))
                async with db.execute(
                    f"SELECT * FROM cards WHERE hash IN ({placeholders})",
                    hash_strs
                ) as cursor:
                    rows = await cursor.fetchall()
                    
                    cards = []
                    for row in rows:
                        content = bytes(row['content'])
                        # Attempt to decode as UTF-8 if it looks like text
                        if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                            try:
                                content = content.decode('utf-8')
                            except UnicodeDecodeError:
                                pass  # Keep as bytes if we can't decode
                        
                        # Parse timestamp and ensure UTC
                        g_time = datetime.fromisoformat(row['g_time'])
                        if g_time.tzinfo is None:
                            g_time = g_time.replace(tzinfo=timezone.utc)
                        else:
                            g_time = g_time.astimezone(timezone.utc)
                        
                        cards.append(MCard(
                            content=content,
                            hash=row['hash'],
                            g_time=g_time
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
                        
                        g_time = datetime.fromisoformat(row['g_time'])
                        if g_time.tzinfo is None:
                            g_time = g_time.replace(tzinfo=timezone.utc)
                        
                        cards.append(MCard(
                            content=content,
                            hash=row['hash'],
                            g_time=g_time
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

    async def _cleanup_transaction(self, task_id: int) -> None:
        """Clean up transaction resources."""
        if task_id in self._transaction_connections:
            conn = self._transaction_connections[task_id]
            await conn.close()
            del self._transaction_connections[task_id]
            del self._transaction_levels[task_id]

    @asynccontextmanager
    async def transaction(self):
        """Transaction context manager with support for nested transactions using savepoints."""
        task_id = id(asyncio.current_task())
        
        # Get or create transaction level counter
        level = self._transaction_levels.get(task_id, 0)
        self._transaction_levels[task_id] = level + 1
        
        # Create savepoint name for this level
        savepoint = f"sp_level_{level}"
        
        # Create new connection at outermost level
        is_outermost = level == 0
        if is_outermost:
            conn = await aiosqlite.connect(self.db_path)
            await conn.execute("BEGIN IMMEDIATE")  # Use IMMEDIATE to prevent other writes
            self._transaction_connections[task_id] = conn
        else:
            # Create savepoint for nested transaction
            conn = self._transaction_connections[task_id]
            await conn.execute(f"SAVEPOINT {savepoint}")
        
        try:
            yield
            # Commit at outermost level, release savepoint otherwise
            if is_outermost:
                await self._transaction_connections[task_id].commit()
            else:
                await conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        except:
            # Rollback at outermost level, rollback to savepoint otherwise
            if is_outermost:
                await self._transaction_connections[task_id].rollback()
            else:
                await conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            raise
        finally:
            # Decrement nesting level
            self._transaction_levels[task_id] -= 1
            # Cleanup at outermost level
            if is_outermost:
                await self._cleanup_transaction(task_id)

    async def close(self) -> None:
        """Close all connections."""
        async with self._pool_lock:
            for conn in self._connection_pool:
                await conn.close()
            self._connection_pool.clear()
            
            # Close any active transaction connections
            for conn in self._transaction_connections.values():
                await conn.close()
            self._transaction_connections.clear()
            self._transaction_levels.clear()
