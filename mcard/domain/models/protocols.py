"""
Core domain protocols for MCard.
"""
from __future__ import annotations
from typing import Protocol, Optional, Any, Union, List, runtime_checkable
from datetime import datetime

from .card import MCard

@runtime_checkable
class CardStore(Protocol):
    """Abstract card store for persistence operations."""
    async def save(self, card: MCard) -> None:
        """Save a card to the store."""
        ...

    async def save_many(self, cards: list[MCard]) -> None:
        """Save multiple cards to the store."""
        ...

    async def get(self, hash_str: str) -> Optional[MCard]:
        """Retrieve a card by its hash from the store."""
        ...

    async def get_many(self, hash_strs: list[str]) -> list[MCard]:
        """Retrieve multiple cards by their hashes from the store."""
        ...

    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[MCard]:
        """Retrieve all cards from the store with optional pagination."""
        ...

    async def list(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[MCard]:
        """List cards with optional time range and pagination."""
        ...

    async def delete(self, hash_str: str) -> None:
        """Delete a card from the store."""
        ...

    async def delete_many(self, hash_strs: list[str]) -> None:
        """Delete multiple cards from the store."""
        ...

    async def search(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[MCard]:
        """Search for cards matching a query."""
        ...

    async def get_by_time_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[MCard]:
        """
        Retrieve cards from the store within a time range.
        
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
    ) -> list[MCard]:
        """
        Retrieve cards from the store created before the specified time.
        
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
    ) -> list[MCard]:
        """
        Retrieve cards from the store created after the specified time.
        
        Args:
            time: Lower bound time (exclusive)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of cards created after the specified time, ordered by g_time DESC
        """
        ...

    async def delete_before_time(self, time: datetime) -> int:
        """
        Delete all cards from the store created before the specified time.
        
        Args:
            time: Upper bound time (exclusive)
            
        Returns:
            Number of cards deleted
        """
        ...

    async def begin_transaction(self) -> None:
        """Begin a store transaction."""
        ...

    async def commit_transaction(self) -> None:
        """Commit the current store transaction."""
        ...

    async def rollback_transaction(self) -> None:
        """Rollback the current store transaction."""
        ...

@runtime_checkable
class ContentTypeService(Protocol):
    """Abstract content type service."""
    def detect_type(self, content: Union[str, bytes]):
        """Detect the content type."""
        ...

    def validate_content(self, content: Any):
        """Validate the content."""
        ...

@runtime_checkable
class HashingService(Protocol):
    """Protocol for hashing service operations."""
    
    async def hash_content(self, content: bytes) -> str:
        """
        Hash the given content.
        
        Args:
            content: Content to hash
            
        Returns:
            Hash string
        """
        ...

    async def validate_hash(self, hash_str: str) -> bool:
        """
        Validate a hash string.
        
        Args:
            hash_str: Hash string to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...

    async def validate_content(self, content: Any) -> bool:
        """
        Validate the content for hashing.
        
        Args:
            content: Content to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...

@runtime_checkable
class CardRepository(Protocol):
    """Protocol for card repository operations."""
    async def save(self, card: MCard) -> None:
        """Save a card to the repository."""
        ...

    async def get(self, card_id: str) -> Optional[MCard]:
        """Retrieve a card by its ID."""
        ...

    async def delete(self, card_id: str) -> None:
        """Delete a card by its ID."""
        ...

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[MCard]:
        """List cards with optional pagination."""
        ...

    async def search(self, query: str) -> list[MCard]:
        """Search for cards based on a query."""
        ...

    async def save_many(self, cards: List[MCard]) -> None:
        """Save multiple cards in a batch."""
        ...
