"""
Hashing service protocol.
"""
from __future__ import annotations
from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class HashingService(Protocol):
    """Abstract hashing service."""
    def __init__(self, settings: Any):
        """Initialize the hashing service."""
        pass

    async def hash_content(self, content: bytes) -> str:
        """Hash the given content."""
        ...

    async def validate_hash(self, hash_str: str) -> bool:
        """Validate a hash string."""
        ...

    async def next_level_hash(self) -> 'HashingService':
        """Get the next level hashing service with a stronger algorithm.
        
        Returns:
            A new HashingService instance with the next stronger algorithm
        """
        ...
