"""
Core domain protocols for MCard.
"""
from typing import Protocol, Optional, Any, Union, List
from datetime import datetime

class HashingService(Protocol):
    """Abstract hashing service."""
    def hash_content(self, content: bytes) -> str:
        """Hash the given content."""
        ...

    def validate_hash(self, hash_str: str) -> bool:
        """Validate a hash string."""
        ...

class CardRepository(Protocol):
    """Abstract card repository."""
    async def save(self, card: 'MCard') -> None:
        """Save a card to the repository."""
        ...

    async def save_many(self, cards: list['MCard']) -> None:
        """Save multiple cards to the repository."""
        ...

    async def get(self, hash_str: str) -> Optional['MCard']:
        """Retrieve a card by its hash."""
        ...

    async def get_many(self, hash_strs: list[str]) -> list['MCard']:
        """Retrieve multiple cards by their hashes."""
        ...

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list['MCard']:
        """Retrieve all cards with optional pagination."""
        ...

    async def get_by_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list['MCard']:
        """
        Retrieve cards within a time range.
        
        Args:
            start_time: Start of time range (inclusive). If None, no lower bound.
            end_time: End of time range (inclusive). If None, no upper bound.
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of cards within the specified time range, ordered by g_time DESC
        """
        ...

    async def get_before_time(
        self,
        time: datetime,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list['MCard']:
        """
        Retrieve cards created before the specified time.
        
        Args:
            time: Upper bound time (exclusive)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of cards created before the specified time, ordered by g_time DESC
        """
        ...

    async def get_after_time(
        self,
        time: datetime,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list['MCard']:
        """
        Retrieve cards created after the specified time.
        
        Args:
            time: Lower bound time (exclusive)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of cards created after the specified time, ordered by g_time DESC
        """
        ...

    async def delete(self, hash_str: str) -> None:
        """Delete a card by its hash."""
        ...

    async def delete_many(self, hash_strs: list[str]) -> None:
        """Delete multiple cards by their hashes."""
        ...

    async def delete_before_time(self, time: datetime) -> int:
        """
        Delete all cards created before the specified time.
        
        Args:
            time: Upper bound time (exclusive)
            
        Returns:
            Number of cards deleted
        """
        ...

    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        ...

    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        ...

class ContentTypeService(Protocol):
    """Abstract content type service."""
    def detect_type(self, content: Union[str, bytes]) -> str:
        """Detect the content type."""
        ...

    def validate_content(self, content: Any) -> bool:
        """Validate the content."""
        ...
