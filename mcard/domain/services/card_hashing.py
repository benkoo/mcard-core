"""Card hashing service."""
import asyncio
from typing import Optional
import hashlib

from ..models.hashing_protocol import HashingService
from .hashing import get_hashing_service

def compute_hash(content: bytes) -> str:
    """Compute hash for content using the configured hashing service."""
    # Since the MCard class is synchronous, we'll use a simpler hashing approach
    # to avoid event loop issues. We'll use the same algorithm as the hashing service.
    hashing_service = get_hashing_service()
    algorithm = hashing_service.settings.algorithm

    # Use hashlib directly
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()
