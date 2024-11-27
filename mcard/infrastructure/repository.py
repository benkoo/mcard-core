"""
Repository implementation for MCard.
"""
from typing import Optional, List
from datetime import datetime
import logging
import sqlite3

from ..domain.models.card import MCard
from ..domain.models.protocols import CardRepository

class SQLiteInMemoryRepository(CardRepository):
    def __init__(self):
        self.connection = sqlite3.connect(':memory:')
        self._init_db()

    def _init_db(self):
        with self.connection as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mcard (
                    hash TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    g_time TEXT NOT NULL
                )
            ''')

    async def save(self, card: MCard) -> None:
        """Save a card to the SQLite in-memory database."""
        logging.debug(f"Saving card with hash: {card.hash}")
        logging.debug(f"Repository state before saving: {[MCard(content=bytes(row[1]), hash=row[0], g_time=row[2]) for row in self.connection.execute('SELECT hash, content, g_time FROM mcard').fetchall()]}")
        with self.connection as conn:
            conn.execute(
                'INSERT OR REPLACE INTO mcard (hash, content, g_time) VALUES (?, ?, ?)',
                (card.hash, sqlite3.Binary(card.content.encode('utf-8')), card.g_time)
            )
        logging.debug(f"Card with hash {card.hash} saved successfully.")
        logging.debug(f"Repository state after saving: {[MCard(content=bytes(row[1]), hash=row[0], g_time=row[2]) for row in self.connection.execute('SELECT hash, content, g_time FROM mcard').fetchall()]}")

    async def save_many(self, cards: list[MCard]) -> None:
        """Save multiple cards to the repository."""
        for card in cards:
            await self.save(card)

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash."""
        logging.debug(f"Attempting to retrieve card with hash: {hash_str}")
        cursor = self.connection.execute('SELECT hash, content, g_time FROM mcard WHERE hash = ?', (hash_str,))
        row = cursor.fetchone()
        if row:
            logging.debug(f"Card retrieved: {row}")
            content = bytes(row[1])
            g_time = row[2]
            return MCard(content=content, hash=row[0], g_time=g_time)
        return None

    async def get_many(self, hash_strs: list[str]) -> list[MCard]:
        """Retrieve multiple cards by their hashes."""
        return [await self.get(h) for h in hash_strs if await self.get(h)]

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[MCard]:
        """Retrieve all cards with optional pagination."""
        query = 'SELECT hash, content, g_time FROM mcard ORDER BY g_time DESC'
        params = []
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
            if offset is not None:
                query += ' OFFSET ?'
                params.append(offset)
        cursor = self.connection.execute(query, params)
        return [MCard(content=bytes(row[1]), hash=row[0], g_time=row[2]) for row in cursor.fetchall()]

    async def get_by_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[MCard]:
        """Retrieve cards within a time range."""
        query = 'SELECT hash, content, g_time FROM mcard'
        params = []
        if start_time:
            query += ' WHERE g_time >= ?'
            params.append(start_time.isoformat())
            if end_time:
                query += ' AND g_time <= ?'
                params.append(end_time.isoformat())
        else:
            if end_time:
                query += ' WHERE g_time <= ?'
                params.append(end_time.isoformat())
        query += ' ORDER BY g_time DESC'
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
            if offset is not None:
                query += ' OFFSET ?'
                params.append(offset)
        cursor = self.connection.execute(query, params)
        return [MCard(content=bytes(row[1]), hash=row[0], g_time=row[2]) for row in cursor.fetchall()]

    async def list(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """Retrieve cards with optional time range and pagination."""
        return await self.get_by_time_range(start_time=start_time, end_time=end_time, limit=limit, offset=offset)

    async def delete(self, card: MCard) -> None:
        """Delete a card from the repository."""
        if await self.get(card.hash):
            with self.connection as conn:
                conn.execute('DELETE FROM mcard WHERE hash = ?', (card.hash,))

    async def delete_many(self, hash_strs: List[str]) -> None:
        """Delete multiple cards from the repository."""
        with self.connection as conn:
            conn.executemany('DELETE FROM mcard WHERE hash = ?', [(h,) for h in hash_strs])

# Global variable to hold the shared repository instance
_shared_repository_instance = None

async def get_repository() -> CardRepository:
    """Get a repository instance."""
    global _shared_repository_instance
    if _shared_repository_instance is None:
        _shared_repository_instance = SQLiteInMemoryRepository()
    return _shared_repository_instance
