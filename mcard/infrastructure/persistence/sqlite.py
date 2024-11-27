"""
SQLite implementation of the card repository.
"""
import asyncio
import sqlite3
import aiosqlite
from typing import Optional, List, Union
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from ...domain.models.card import MCard
from ...domain.models.exceptions import StorageError, ValidationError
from ...domain.services.hashing import get_hashing_service
from dateutil import parser
import logging
import time

class SQLiteCardRepository:
    """SQLite implementation of the card repository."""

    def __init__(self, db_path: str):
        """Initialize the repository."""
        self.db_path = db_path
        self._connection = None
        self._lock = asyncio.Lock()
        self._init_done = False
        self.max_content_size = 10 * 1024 * 1024  # 10MB
        self.connection_pool_limit = 5  # Example limit, adjust based on requirements

    async def close_connection(self):
        """Close the database connection if it exists."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a database connection with retry logic."""
        try:
            if self._connection is None:
                self._connection = await aiosqlite.connect(
                    self.db_path,
                    timeout=30.0,  # Increased timeout for busy waiting
                )
                await self._connection.execute("PRAGMA journal_mode=WAL")
                await self._connection.execute("PRAGMA busy_timeout=10000")  # 10 second timeout
                self._connection.row_factory = aiosqlite.Row
            # Test if connection is valid
            await self._connection.execute("SELECT 1")
            return self._connection
        except (sqlite3.Error, AttributeError) as e:
            # Connection is invalid, close it and create a new one
            await self.close_connection()
            try:
                self._connection = await aiosqlite.connect(
                    self.db_path,
                    timeout=30.0,
                )
                await self._connection.execute("PRAGMA journal_mode=WAL")
                await self._connection.execute("PRAGMA busy_timeout=10000")
                self._connection.row_factory = aiosqlite.Row
                return self._connection
            except Exception as e:
                raise StorageError(f"Failed to connect to database: {str(e)}") from e

    async def _init_db(self):
        """Initialize the database schema."""
        logging.debug("Initializing database schema...")
        async with self._lock:
            conn = await self._get_connection()
            try:
                await conn.execute("CREATE TABLE IF NOT EXISTS cards (hash TEXT PRIMARY KEY, content BLOB, g_time TEXT)")
                await conn.commit()
                logging.debug("Database schema initialized successfully.")
            except Exception as e:
                logging.error(f"Error initializing database schema: {e}")
            logging.debug("Database schema initialized successfully")
            self._init_done = True

    def _validate_content_size(self, content: Union[bytes, str]) -> None:
        """Validate content size."""
        size = len(content.encode('utf-8') if isinstance(content, str) else content)
        if size > self.max_content_size:
            raise ValidationError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")

    def _encode_content(self, content: Union[bytes, str]) -> bytes:
        """Encode content as bytes."""
        return content.encode('utf-8') if isinstance(content, str) else content

    async def __aenter__(self):
        """Enter async context."""
        logging.debug("Entering async context and checking initialization")
        if not self._init_done:
            logging.debug("Database not initialized, calling _init_db")
            await self._init_db()
        else:
            logging.debug("Database already initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._connection is not None:
            logging.debug("Closing database connection")
            try:
                await self._connection.close()
                logging.debug("Database connection closed successfully")
            except Exception as e:
                logging.error(f"Error closing connection: {e}")
            finally:
                self._connection = None
                self._init_done = False

    @asynccontextmanager
    async def transaction(self):
        """Transaction context manager."""
        logging.debug("Acquiring lock for transaction")
        async with self._lock:
            conn = await self._get_connection()
            try:
                logging.debug("Starting transaction")
                await conn.execute("BEGIN IMMEDIATE")
                yield
                logging.debug("Committing transaction")
                await conn.commit()
            except Exception:
                logging.debug("Rolling back transaction due to exception")
                await conn.rollback()
                raise

    async def save(self, card: MCard) -> None:
        """Save a card to the database."""
        try:
            content = card.content
            self._validate_content_size(content)
            
            # Encode content as bytes for hashing and storage
            encoded_content = self._encode_content(content)
            
            # Compute hash if needed
            if card.hash == "temp_hash":
                hashing_service = get_hashing_service()
                computed_hash = hashing_service.hash_content_sync(encoded_content)
                card = MCard(content=card.content, hash=computed_hash, g_time=card.g_time)

            # Convert g_time to a datetime object if it's a string
            if isinstance(card.g_time, str):
                card_g_time = parser.parse(card.g_time)
            else:
                card_g_time = card.g_time

            # Remove timezone or convert to UTC if necessary
            card_g_time = card_g_time.replace(tzinfo=None)
            card_g_time = datetime.fromisoformat(card_g_time.isoformat())

            async with self._lock:
                conn = await self._get_connection()
                await conn.execute(
                    "INSERT OR REPLACE INTO cards (hash, content, g_time) VALUES (?, ?, ?)",
                    (card.hash, sqlite3.Binary(encoded_content), card_g_time.isoformat())
                )
                await conn.commit()
        except Exception as e:
            raise StorageError(f"Failed to save card: {str(e)}")

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        if not isinstance(hash_str, str):
            raise StorageError("Hash must be a string")

        try:
            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.execute(
                    "SELECT hash, content, g_time FROM cards WHERE hash = ?",
                    (hash_str,)
                )
                row = await cursor.fetchone()

                if row is None:
                    raise StorageError(f"Card with hash {hash_str} not found.")

                content = bytes(row['content'])
                # Attempt to decode as UTF-8 if it looks like text
                if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        pass  # Keep as bytes if we can't decode

                # Parse timestamp
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
        except Exception as e:
            raise StorageError(f"Failed to retrieve card: {str(e)}")

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards at once."""
        if not cards:
            return

        # Log the start of the batch save operation
        logging.debug(f"Starting batch save for {len(cards)} cards.")
        
        # Log the time taken for encoding and hashing
        encoding_start_time = time.time()
        
        new_cards = []
        values = []
        for card in cards:
            content = card.content
            self._validate_content_size(content)

            # Encode content as bytes for hashing and storage
            encoded_content = self._encode_content(content)
            
            # Compute hash if needed
            if card.hash == "temp_hash":
                hashing_service = get_hashing_service()
                computed_hash = hashing_service.hash_content_sync(encoded_content)
                card = MCard(content=card.content, hash=computed_hash, g_time=card.g_time)
            
            # Convert g_time to a datetime object if it's a string
            if isinstance(card.g_time, str):
                card_g_time = parser.parse(card.g_time)
            else:
                card_g_time = card.g_time

            # Remove timezone or convert to UTC if necessary
            card_g_time = card_g_time.replace(tzinfo=None)
            card_g_time = datetime.fromisoformat(card_g_time.isoformat())

            new_cards.append(card)
            values.append((
                card.hash,
                sqlite3.Binary(encoded_content),
                card_g_time.isoformat()
            ))

        encoding_duration = time.time() - encoding_start_time
        logging.debug(f"Encoding and hashing completed in {encoding_duration:.2f} seconds.")

        async with self._lock:
            conn = await self._get_connection()
            await conn.executemany(
                "INSERT OR REPLACE INTO cards (hash, content, g_time) VALUES (?, ?, ?)",
                values
            )
            await conn.commit()
        
        # Log the end of the batch save operation
        logging.debug("Batch save operation completed.")
        
        # Update the input list with new cards that have computed hashes
        cards.clear()
        cards.extend(new_cards)

    async def get_many(self, hash_strs: List[str]) -> List[MCard]:
        """Retrieve multiple cards by their hashes."""
        if not hash_strs:
            return []

        if not all(isinstance(h, str) for h in hash_strs):
            raise StorageError("All hashes must be strings")

        try:
            async with self._lock:
                conn = await self._get_connection()
                placeholders = ','.join('?' * len(hash_strs))
                cursor = await conn.execute(
                    f"SELECT * FROM cards WHERE hash IN ({placeholders})",
                    hash_strs
                )
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
        except Exception as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Retrieve all cards with pagination support."""
        try:
            # Log the start of the get_all operation
            logging.debug("Starting get_all operation.")
            
            # Log the time taken for query execution
            query_start_time = time.time()
            
            async with self._lock:
                conn = await self._get_connection()
                query = "SELECT * FROM cards ORDER BY g_time DESC"
                params = []
                
                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                    if offset is not None:
                        query += " OFFSET ?"
                        params.append(offset)

                cards = []
                cursor = await conn.execute(query, params)
                async for row in cursor:
                    content = bytes(row['content'])
                    # Attempt to decode as UTF-8 if it looks like text
                    if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                        try:
                            content = content.decode('utf-8')
                        except UnicodeDecodeError:
                            pass  # Keep as bytes if we can't decode
                        
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

            query_duration = time.time() - query_start_time
            logging.debug(f"Query execution completed in {query_duration:.2f} seconds.")

            # Log the end of the get_all operation
            logging.debug("get_all operation completed.")
            return cards
        except Exception as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    async def delete(self, hash_str: str) -> None:
        """Delete a card by its hash."""
        try:
            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.execute(
                    "SELECT 1 FROM cards WHERE hash = ?",
                    (hash_str,)
                )
                if await cursor.fetchone() is None:
                    raise StorageError(f"Card with hash {hash_str} not found.")
                await conn.execute(
                    "DELETE FROM cards WHERE hash = ?",
                    (hash_str,)
                )
                await conn.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete card: {str(e)}")

    async def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards by their hashes."""
        if not hash_strs:
            return

        try:
            async with self._lock:
                conn = await self._get_connection()
                placeholders = ','.join('?' * len(hash_strs))
                await conn.execute(
                    f"DELETE FROM cards WHERE hash IN ({placeholders})",
                    hash_strs
                )
                await conn.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete cards: {str(e)}")
