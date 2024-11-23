"""SQLite storage implementation for MCard."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time
from typing import List, Optional, Tuple
import sqlite3
from .core import MCard
from . import config

class MCardRecord:
    """SQLite model for storing MCard instances."""
    def __init__(self, content_hash, content, time_claimed, is_binary):
        self.content_hash = content_hash
        self.content = content
        self.time_claimed = time_claimed
        self.is_binary = is_binary

    def to_mcard(self) -> MCard:
        """Convert database record to MCard instance."""
        content = self.content
        if not self.is_binary:
            content = content.decode('utf-8')
        
        # Ensure timezone information is preserved and converted to local timezone
        time_claimed = self.time_claimed
        if time_claimed.tzinfo is None:
            time_claimed = time_claimed.replace(tzinfo=timezone.utc)
        time_claimed = time_claimed.astimezone()
        
        return MCard(
            content=content,
            content_hash=self.content_hash,
            time_claimed=time_claimed
        )

class MCardStorage:
    """Storage manager for MCard instances."""
    
    def __init__(self, db_path: Optional[str] = None, test: bool = False):
        """Initialize storage with database path."""
        # Load environment variables if not already loaded
        config.load_config()
        
        # Use provided db_path or get from environment
        self.db_path = db_path if db_path is not None else config.get_db_path(test)

        def adapt_datetime(val):
            """Store datetime with its timezone information."""
            if val.tzinfo is None:
                # If no timezone info, assume it's in local time
                val = val.replace(tzinfo=datetime.now().astimezone().tzinfo)
            return val.isoformat()  # Store with timezone info intact

        def convert_datetime(val):
            """Convert ISO format string back to datetime, preserving timezone."""
            if isinstance(val, bytes):
                val = val.decode('utf-8')
            return datetime.fromisoformat(val)  # This preserves the original timezone

        sqlite3.register_adapter(datetime, adapt_datetime)
        sqlite3.register_converter("DATETIME", convert_datetime)
        
        self.conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcards (
                content_hash TEXT PRIMARY KEY,
                content BLOB,
                time_claimed DATETIME,
                is_binary INTEGER
            )
        ''')

    def save(self, mcard: MCard) -> bool:
        """
        Save MCard instance to database if it doesn't already exist.
        
        Returns:
            bool: True if the record was saved, False if it already existed
        """
        try:
            # Check if record already exists
            self.cursor.execute('SELECT 1 FROM mcards WHERE content_hash = ?', (mcard.content_hash,))
            if self.cursor.fetchone():
                return False

            # Convert content to bytes if it's not already
            content = mcard.content
            is_binary = isinstance(content, bytes)
            if isinstance(content, str):
                content = content.encode('utf-8')
            elif not isinstance(content, bytes):
                content = str(content).encode('utf-8')

            self.cursor.execute('''
                INSERT INTO mcards (content_hash, content, time_claimed, is_binary)
                VALUES (?, ?, ?, ?)
            ''', (mcard.content_hash, content, mcard.time_claimed, int(is_binary)))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return False

    def save_many(self, mcards: List[MCard]) -> Tuple[int, int]:
        """
        Save multiple MCard instances to database, skipping existing ones.
        
        Returns:
            Tuple[int, int]: (number of records saved, number of records skipped)
        """
        saved = 0
        skipped = 0
        
        # Get existing hashes
        try:
            self.cursor.execute('SELECT content_hash FROM mcards')
            existing_hashes = {row[0] for row in self.cursor.fetchall()}
        except sqlite3.Error as e:
            print(f"Error getting existing hashes: {e}")
            return 0, 0
        
        # Process each record
        for mcard in mcards:
            try:
                if mcard.content_hash in existing_hashes:
                    skipped += 1
                    continue
                
                # Convert content to bytes if it's not already
                content = mcard.content
                is_binary = isinstance(content, bytes)
                if isinstance(content, str):
                    content = content.encode('utf-8')
                elif not isinstance(content, bytes):
                    content = str(content).encode('utf-8')

                self.cursor.execute('''
                    INSERT INTO mcards (content_hash, content, time_claimed, is_binary)
                    VALUES (?, ?, ?, ?)
                ''', (mcard.content_hash, content, mcard.time_claimed, int(is_binary)))
                saved += 1
                existing_hashes.add(mcard.content_hash)  # Update existing hashes
            except sqlite3.Error as e:
                print(f"Error saving record with hash {mcard.content_hash}: {e}")
                skipped += 1
        
        try:
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error committing changes: {e}")
            return 0, 0
        
        return saved, skipped

    def get(self, content_hash: str) -> Optional[MCard]:
        """Retrieve MCard by content hash."""
        try:
            self.cursor.execute('SELECT * FROM mcards WHERE content_hash = ?', (content_hash,))
            record = self.cursor.fetchone()
            if not record:
                return None

            # Convert content based on original type
            content = record[1]
            if not record[3]:
                content = content.decode('utf-8')

            return MCard(
                content=content,
                content_hash=record[0],
                time_claimed=record[2]  # Already a datetime with original timezone
            )
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return None

    def get_all(self) -> List[MCard]:
        """Retrieve all MCard instances."""
        try:
            self.cursor.execute('SELECT * FROM mcards')
            records = self.cursor.fetchall()
            return [
                MCard(
                    content=record[1] if record[3] else record[1].decode('utf-8'),
                    content_hash=record[0],
                    time_claimed=record[2]  # Already a datetime with original timezone
                )
                for record in records
            ]
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return []

    def delete(self, content_hash: str) -> bool:
        """Delete MCard by content hash."""
        try:
            self.cursor.execute('DELETE FROM mcards WHERE content_hash = ?', (content_hash,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return False
