"""MCard model definition."""
import hashlib
from datetime import datetime, timezone
from typing import Union, Optional, Dict, Any

from ..models.exceptions import ValidationError
from ..services.card_hashing import compute_hash

class MCard:
    """MCard model."""

    def __init__(self, content: Union[str, bytes], hash: Optional[str] = None, g_time: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Initialize MCard."""
        if content is None:
            raise ValidationError("Card content cannot be None")

        # Convert content to bytes if it's a string
        if isinstance(content, str):
            self._content = content.encode('utf-8')
        elif isinstance(content, bytes):
            self._content = content
        else:
            self._content = str(content).encode('utf-8')

        # Compute hash if not provided
        self._hash = hash or compute_hash(self._content)
        self._g_time = self._parse_time(g_time) if g_time else datetime.now(timezone.utc)
        self._metadata = metadata or {}

    @property
    def content(self) -> Union[str, bytes]:
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

    def __str__(self) -> str:
        """String representation of MCard."""
        try:
            content_preview = self._content.decode('utf-8')[:50]
        except UnicodeDecodeError:
            content_preview = str(self._content)[:50]

        if len(content_preview) < len(str(self._content)):
            content_preview += "..."
        return f"MCard(hash={self.hash}, g_time={self.g_time}, content={content_preview}, metadata={self.metadata})"
