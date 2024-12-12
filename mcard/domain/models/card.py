"""MCard model definition."""
import hashlib
from datetime import datetime, timezone
from typing import Union, Optional, Dict, Any, List
from pydantic import BaseModel

from ..models.exceptions import ValidationError
from ..services.card_hashing import compute_hash

class CardCreate(BaseModel):
    """Request model for creating a new card."""
    content: str

class MCard:
    """MCard domain model."""

    def __init__(self, content: Union[str, bytes], hash: Optional[str] = None, g_time: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Initialize MCard."""
        if content is None:
            raise ValidationError("Card content cannot be None")

        # Convert content to string if it's bytes
        if isinstance(content, bytes):
            self._content = content.decode('utf-8')
        else:
            self._content = str(content)

        # Compute hash if not provided
        content_bytes = self._content.encode('utf-8')
        self._hash = hash or compute_hash(content_bytes)
        self._g_time = self._parse_time(g_time) if g_time else datetime.now(timezone.utc)
        self._metadata = metadata or {}

    @property
    def content(self) -> str:
        """Get card content."""
        return self._content

    @property
    def hash(self) -> str:
        """Get card hash."""
        return self._hash

    @hash.setter
    def hash(self, value: str):
        """Set card hash."""
        if not value:
            raise ValidationError("Hash cannot be empty")
        self._hash = value

    @property
    def g_time(self) -> str:
        """Get card global time."""
        return self._g_time.isoformat()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get card metadata."""
        return self._metadata

    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        """Set card metadata."""
        if not isinstance(value, dict):
            raise ValidationError("Metadata must be a dictionary")
        self._metadata = value

    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime."""
        try:
            dt = datetime.fromisoformat(time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid time format: {str(e)}")

    def to_api_response(self) -> 'CardResponse':
        """Convert to API response model."""
        return CardResponse(
            hash=self.hash,
            content=self.content,
            g_time=self.g_time,
            metadata=self.metadata
        )

    def __str__(self) -> str:
        """String representation of MCard."""
        content_preview = self._content[:50]

        if len(content_preview) < len(self._content):
            content_preview += "..."
        return f"MCard(hash={self.hash}, g_time={self.g_time}, content={content_preview}, metadata={self.metadata})"

class CardResponse(BaseModel):
    """API response model for card data."""
    hash: str
    content: str
    g_time: str
    metadata: Dict = {}

class PaginatedCardsResponse(BaseModel):
    """Response model for paginated card listings."""
    items: List[CardResponse]
    total: int
    page: int
    page_size: int
