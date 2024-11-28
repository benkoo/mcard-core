"""SQLite repository implementation."""
import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Optional
import threading

from ...domain.models.card import MCard
from ...domain.models.exceptions import StorageError, ValidationError
from ...domain.models.protocols import CardRepository

class SQLiteRepository(CardRepository):
    """SQLite-based repository implementation."""

    def __init__(self, db_path: str, max_content_size: int = 100 * 1024 * 1024):  # 100MB default
        """Initialize the repository with a database path."""
        self._db_path = db_path
        self._local = threading.local()
        self._max_content_size = max_content_size
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        self._ensure_table()

    @property
    def connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(self._db_path)
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    @property
    def max_content_size(self) -> int:
        """Get maximum allowed content size."""
        return self._max_content_size

    def _ensure_table(self) -> None:
        """Ensure the required table exists."""
        try:
            with self.connection as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS card (
                        hash TEXT PRIMARY KEY,
                        content BLOB NOT NULL,
                        g_time TEXT NOT NULL
                    )
                """)
        except Exception as e:
            raise StorageError(f"Failed to create table: {str(e)}")

    async def get(self, card_hash: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        try:
            cursor = self.connection.execute(
                "SELECT hash, content, g_time FROM card WHERE hash = ?",
                (card_hash,)
            )
            row = cursor.fetchone()
            if row is None:
                raise StorageError(f"Card with hash {card_hash} not found.")

            content = bytes(row['content'])
            # Attempt to decode as UTF-8 if it looks like text
            if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    pass  # Keep as bytes if we can't decode

            return MCard(
                content=content,
                hash=row['hash'],
                g_time=row['g_time']
            )
        except Exception as e:
            raise StorageError(f"Failed to retrieve card: {str(e)}")

    async def save(self, card: MCard) -> None:
        """Save a card to the database."""
        try:
            # Convert content to bytes if it's a string
            content = card.content.encode() if isinstance(card.content, str) else card.content
            
            if len(content) > self.max_content_size:
                raise ValidationError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")
            
            with self.connection as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO card (hash, content, g_time) VALUES (?, ?, ?)",
                    (card.hash, content, str(card.g_time))
                )
        except ValidationError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to save card: {str(e)}")

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards at once."""
        try:
            values = []
            for card in cards:
                content = card.content.encode() if isinstance(card.content, str) else card.content
                if len(content) > self.max_content_size:
                    raise ValidationError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")
                values.append((card.hash, content, str(card.g_time)))

            with self.connection as conn:
                conn.execute("BEGIN TRANSACTION")
                try:
                    conn.executemany(
                        "INSERT OR REPLACE INTO card (hash, content, g_time) VALUES (?, ?, ?)",
                        values
                    )
                    conn.execute("COMMIT")
                except Exception as e:
                    conn.execute("ROLLBACK")
                    raise StorageError(f"Failed to save cards: {str(e)}")
        except ValidationError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to save cards: {str(e)}")

    async def get_many(self, hashes: List[str]) -> List[MCard]:
        """Retrieve multiple cards by their hashes."""
        try:
            cards = []
            placeholders = ','.join('?' * len(hashes))
            cursor = self.connection.execute(
                f"SELECT hash, content, g_time FROM card WHERE hash IN ({placeholders}) ORDER BY g_time DESC",
                hashes
            )
            for row in cursor:
                content = bytes(row['content'])
                if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        pass
                cards.append(MCard(
                    content=content,
                    hash=row['hash'],
                    g_time=row['g_time']
                ))
            return cards
        except Exception as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    async def delete(self, card_hash: str) -> None:
        """Delete a card from the database."""
        try:
            with self.connection as conn:
                cursor = conn.execute(
                    "DELETE FROM card WHERE hash = ?",
                    (card_hash,)
                )
                if cursor.rowcount == 0:
                    raise StorageError(f"Card with hash {card_hash} not found.")
        except StorageError as e:
            raise StorageError(f"Failed to delete card: {str(e)}")
        except Exception as e:
            raise StorageError(f"Failed to delete card: {str(e)}")

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Retrieve all cards with optional pagination."""
        try:
            query = "SELECT hash, content, g_time FROM card ORDER BY g_time DESC"
            params = []
            
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)
            
            cursor = self.connection.execute(query, params)
            cards = []
            for row in cursor:
                content = bytes(row['content'])
                if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        pass
                cards.append(MCard(
                    content=content,
                    hash=row['hash'],
                    g_time=row['g_time']
                ))
            return cards
        except Exception as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    async def remove(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        try:
            with self.connection as conn:
                cursor = conn.execute("DELETE FROM card WHERE hash = ?", (hash_str,))
                if cursor.rowcount == 0:
                    raise StorageError(f"Card with hash {hash_str} not found")
        except Exception as e:
            raise StorageError(f"Failed to remove card: {e}")

    async def close_connection(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection"):
            try:
                self._local.connection.close()
                delattr(self._local, "connection")
            except Exception as e:
                logging.error(f"Error closing database connection: {e}")

    def __del__(self):
        """Clean up database connections."""
        if hasattr(self._local, "connection"):
            try:
                self._local.connection.close()
            except Exception:
                pass  # Ignore cleanup errors
