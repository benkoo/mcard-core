"""
SQLite implementation of the card repository.
"""
import sqlite3
import logging
from typing import Optional, List, Union
from datetime import datetime, timezone
from dateutil import parser
from ...domain.models.card import MCard
from ...domain.models.exceptions import StorageError, ValidationError
from ...domain.services.hashing import get_hashing_service
from .schema_initializer import SchemaInitializer, initialize_schema
import time

class SQLiteRepository:
    """SQLite implementation of the card repository using synchronous sqlite3."""

    def __init__(self, db_path: str):
        """Initialize the repository."""
        self.db_path = db_path
        self.max_content_size = 10 * 1024 * 1024  # 10MB
        self.connection = sqlite3.connect(self.db_path)
        self._init_db()
        SchemaInitializer.initialize_schema(self.connection)

    def _init_db(self):
        """Initialize the database schema."""
        initialize_schema(self.connection)

    def _validate_content_size(self, content: Union[bytes, str]) -> None:
        """Validate content size."""
        size = len(content.encode('utf-8') if isinstance(content, str) else content)
        if size > self.max_content_size:
            raise ValidationError(f"Content size exceeds maximum limit of {self.max_content_size} bytes")

    def _encode_content(self, content: Union[bytes, str]) -> bytes:
        """Encode content as bytes."""
        return content.encode('utf-8') if isinstance(content, str) else content

    def save(self, card: MCard) -> None:
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

            self.connection.execute(
                "INSERT OR REPLACE INTO card (hash, content, g_time) VALUES (?, ?, ?)",
                (card.hash, sqlite3.Binary(encoded_content), card_g_time.isoformat())
            )
            self.connection.commit()
        except ValidationError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to save card: {str(e)}")

    def get(self, card_hash: str) -> Optional[MCard]:
        """Retrieve a card from the database by its hash."""
        try:
            cursor = self.connection.execute(
                "SELECT hash, content, g_time FROM card WHERE hash = ?",
                (card_hash,)
            )
            row = cursor.fetchone()
            if row is None:
                raise StorageError(f"Card with hash {card_hash} not found.")

            content = bytes(row[1])  # Access content by index
            # Attempt to decode as UTF-8 if it looks like text
            if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    pass  # Keep as bytes if we can't decode

            # Parse timestamp
            g_time = datetime.fromisoformat(row[2])
            if g_time.tzinfo is None:
                g_time = g_time.replace(tzinfo=timezone.utc)
            else:
                g_time = g_time.astimezone(timezone.utc)

            return MCard(
                content=content,
                hash=row[0],  # Access hash by index
                g_time=g_time
            )
        except Exception as e:
            raise StorageError(f"Failed to retrieve card: {str(e)}")

    def save_many(self, cards: List[MCard]) -> None:
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

        self.connection.executemany(
            "INSERT OR REPLACE INTO card (hash, content, g_time) VALUES (?, ?, ?)",
            values
        )
        self.connection.commit()
        
        # Log the end of the batch save operation
        logging.debug("Batch save operation completed.")
        
        # Update the input list with new cards that have computed hashes
        cards.clear()
        cards.extend(new_cards)

    def get_many(self, hash_strs: List[str]) -> List[MCard]:
        """Retrieve multiple cards by their hashes."""
        if not hash_strs:
            return []

        if not all(isinstance(h, str) for h in hash_strs):
            raise StorageError("All hashes must be strings")

        try:
            placeholders = ','.join('?' * len(hash_strs))
            cursor = self.connection.execute(
                f"SELECT * FROM card WHERE hash IN ({placeholders}) ORDER BY g_time DESC",
                hash_strs
            )
            rows = cursor.fetchall()

            cards = []
            for row in rows:
                content = row[1]  # Access content by index
                # Log content type
                logging.debug(f"Retrieved content type: {type(content)}")
                # Decode content if it's stored as bytes and can be decoded
                if isinstance(content, bytes):
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        pass  # Keep as bytes if we can't decode

                # Parse timestamp and ensure UTC
                g_time = datetime.fromisoformat(row[2])
                if g_time.tzinfo is None:
                    g_time = g_time.replace(tzinfo=timezone.utc)
                else:
                    g_time = g_time.astimezone(timezone.utc)

                cards.append(MCard(
                    content=content,
                    hash=row[0],  # Access hash by index
                    g_time=g_time
                ))
            return cards
        except Exception as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Retrieve all cards with pagination support."""
        try:
            logging.debug("Starting get_all operation.")
            query_start_time = time.time()

            query = "SELECT * FROM card ORDER BY g_time DESC"
            params = []

            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)

            cards = []
            cursor = self.connection.execute(query, params)
            for row in cursor.fetchall():
                content = bytes(row[1])
                if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        pass

                g_time = datetime.fromisoformat(row[2])
                if g_time.tzinfo is None:
                    g_time = g_time.replace(tzinfo=timezone.utc)
                else:
                    g_time = g_time.astimezone(timezone.utc)

                cards.append(MCard(
                    content=content,
                    hash=row[0],
                    g_time=g_time
                ))

            query_duration = time.time() - query_start_time
            logging.debug(f"Query execution completed in {query_duration:.2f} seconds.")
            logging.debug("get_all operation completed.")
            return cards
        except Exception as e:
            raise StorageError(f"Failed to retrieve cards: {str(e)}")

    def delete(self, hash_str: str) -> None:
        """Delete a card by its hash."""
        try:
            cursor = self.connection.execute(
                "SELECT 1 FROM card WHERE hash = ?",
                (hash_str,)
            )
            if cursor.fetchone() is None:
                raise StorageError(f"Card with hash {hash_str} not found.")
            self.connection.execute(
                "DELETE FROM card WHERE hash = ?",
                (hash_str,)
            )
            self.connection.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete card: {str(e)}")

    def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards by their hashes."""
        if not hash_strs:
            return

        try:
            placeholders = ','.join('?' * len(hash_strs))
            self.connection.execute(
                f"DELETE FROM card WHERE hash IN ({placeholders})",
                hash_strs
            )
            self.connection.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete cards: {str(e)}")
