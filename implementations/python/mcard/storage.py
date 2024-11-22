"""SQLite storage implementation for MCard."""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import sqlalchemy
from sqlalchemy import Column, String, DateTime, LargeBinary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker
from .core import MCard

Base = declarative_base()

class MCardRecord(Base):
    """SQLite model for storing MCard instances."""
    __tablename__ = 'mcards'

    content_hash = Column(String, primary_key=True)
    content = Column(LargeBinary)  
    time_claimed = Column(DateTime(timezone=True))
    is_binary = Column(Boolean, default=False)

    def to_mcard(self) -> MCard:
        """Convert database record to MCard instance."""
        content = self.content
        if not self.is_binary:
            content = content.decode('utf-8')
        
        return MCard(
            content=content,
            content_hash=self.content_hash,
            time_claimed=self.time_claimed
        )

class MCardStorage:
    """Storage manager for MCard instances."""
    
    def __init__(self, db_path: str = "mcards.db"):
        """Initialize storage with database path."""
        self.engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save(self, mcard: MCard) -> bool:
        """
        Save MCard instance to database if it doesn't already exist.
        
        Returns:
            bool: True if the record was saved, False if it already existed
        """
        session = self.Session()
        try:
            # Check if record already exists
            existing_record = session.get(MCardRecord, mcard.content_hash)
            if existing_record:
                return False

            # Convert content to bytes if it's not already
            content = mcard.content
            is_binary = isinstance(content, bytes)
            if isinstance(content, str):
                content = content.encode('utf-8')
            elif not isinstance(content, bytes):
                content = str(content).encode('utf-8')

            record = MCardRecord(
                content_hash=mcard.content_hash,
                content=content,
                time_claimed=mcard.time_claimed,
                is_binary=is_binary
            )
            session.add(record)
            session.commit()
            return True
        finally:
            session.close()

    def save_many(self, mcards: List[MCard]) -> Tuple[int, int]:
        """
        Save multiple MCard instances to database, skipping existing ones.
        
        Returns:
            Tuple[int, int]: (number of records saved, number of records skipped)
        """
        session = self.Session()
        try:
            saved = 0
            skipped = 0
            
            # Get existing hashes
            existing_hashes = {r[0] for r in session.query(MCardRecord.content_hash).all()}
            
            # Process each record
            for mcard in mcards:
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

                record = MCardRecord(
                    content_hash=mcard.content_hash,
                    content=content,
                    time_claimed=mcard.time_claimed,
                    is_binary=is_binary
                )
                session.add(record)
                saved += 1
            
            session.commit()
            return saved, skipped
        finally:
            session.close()

    def get(self, content_hash: str) -> Optional[MCard]:
        """Retrieve MCard by content hash."""
        session = self.Session()
        try:
            record = session.get(MCardRecord, content_hash)
            if not record:
                return None

            # Convert content based on original type
            content = record.content
            if not record.is_binary:
                content = content.decode('utf-8')

            return MCard(
                content=content,
                content_hash=record.content_hash,
                time_claimed=record.time_claimed.replace(tzinfo=timezone.utc)
            )
        finally:
            session.close()

    def get_all(self) -> List[MCard]:
        """Retrieve all MCard instances."""
        session = self.Session()
        try:
            records = session.query(MCardRecord).all()
            return [
                MCard(
                    content=record.content if record.is_binary else record.content.decode('utf-8'),
                    content_hash=record.content_hash,
                    time_claimed=record.time_claimed.replace(tzinfo=timezone.utc)
                )
                for record in records
            ]
        finally:
            session.close()

    def delete(self, content_hash: str) -> bool:
        """Delete MCard by content hash."""
        session = self.Session()
        try:
            record = session.get(MCardRecord, content_hash)
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        finally:
            session.close()
