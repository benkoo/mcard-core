import aiosqlite
from typing import Optional, List
from contextlib import asynccontextmanager
from mcard.domain.models.card import MCard
from mcard.domain.models.exceptions import StorageError
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.infrastructure.persistence.schema_initializer import SchemaInitializer

class AsyncSQLiteWrapper:
    """Asynchronous wrapper for SQLite operations."""
    
    def __init__(self, config: SQLiteConfig):
        """Initialize the wrapper with configuration."""
        self._config = config
        self._connection: Optional[aiosqlite.Connection] = None

    async def __aenter__(self):
        """Initialize database connection and schema on enter."""
        try:
            self._connection = await aiosqlite.connect(
                self._config.db_path,
                isolation_level=None  # autocommit mode
            )
            self._connection.row_factory = aiosqlite.Row
            await SchemaInitializer.initialize_schema(self._connection)
            return self
        except aiosqlite.Error as e:
            if self._connection:
                await self._connection.close()
            raise StorageError(f"Failed to initialize database: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the database connection on exit."""
        if self._connection:
            try:
                await self._connection.close()
            finally:
                self._connection = None

    def _check_connection(self) -> aiosqlite.Connection:
        """Check if connection is initialized."""
        if not self._connection:
            raise StorageError("Database connection not initialized")
        return self._connection

    async def save(self, card: MCard) -> None:
        """Save a card asynchronously."""
        conn = self._check_connection()
        try:
            await conn.execute(
                "INSERT INTO card (hash, content, content_type, g_time) VALUES (?, ?, ?, ?)",
                (card.hash, card.content.encode() if isinstance(card.content, str) else card.content,
                 'text' if isinstance(card.content, str) else 'binary', card.g_time)
            )
            await conn.commit()
        except aiosqlite.IntegrityError as e:
            raise StorageError(f"Card with hash {card.hash} already exists") from e

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards asynchronously."""
        conn = self._check_connection()
        try:
            await conn.executemany(
                "INSERT INTO card (hash, content, content_type, g_time) VALUES (?, ?, ?, ?)",
                [(card.hash, card.content.encode() if isinstance(card.content, str) else card.content,
                  'text' if isinstance(card.content, str) else 'binary', card.g_time) for card in cards]
            )
            await conn.commit()
        except aiosqlite.IntegrityError as e:
            raise StorageError("One or more cards already exist") from e

    async def get(self, hash_value: str) -> Optional[MCard]:
        """Get a card by hash asynchronously."""
        conn = self._check_connection()
        async with conn.execute(
            "SELECT hash, content, content_type, g_time FROM card WHERE hash = ?",
            (hash_value,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return MCard(
                hash=row['hash'],
                content=row['content'].decode() if row['content_type'] == 'text' else row['content'],
                g_time=row['g_time']
            )

    async def get_all(self, content: Optional[str] = None, limit: Optional[int] = None,
                     offset: Optional[int] = None) -> List[MCard]:
        """Get all cards with optional filtering and pagination."""
        conn = self._check_connection()
        query = "SELECT hash, content, content_type, g_time FROM card"
        params = []

        if content:
            query += " WHERE content LIKE ?"
            params.append(f"%{content}%")

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                MCard(
                    hash=row['hash'],
                    content=row['content'].decode() if row['content_type'] == 'text' else row['content'],
                    g_time=row['g_time']
                )
                for row in rows
            ]

    async def delete(self, hash_value: str) -> None:
        """Delete a card asynchronously."""
        conn = self._check_connection()
        await conn.execute("DELETE FROM card WHERE hash = ?", (hash_value,))
        await conn.commit()

    async def delete_all(self) -> None:
        """Delete all cards asynchronously."""
        conn = self._check_connection()
        await conn.execute("DELETE FROM card")
        await conn.commit()