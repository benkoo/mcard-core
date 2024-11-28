"""MCard model definition."""
import hashlib
from datetime import datetime, timezone
from typing import Union, Optional

from ..models.exceptions import ValidationError

class MCard:
    """MCard model."""

    def __init__(self, content: Union[str, bytes], hash: Optional[str] = None, g_time: Optional[str] = None):
        """Initialize MCard."""
        self._content = content
        self._hash = hash or self._compute_hash()
        self._g_time = self._parse_time(g_time) if g_time else datetime.now(timezone.utc)

    @property
    def content(self) -> Union[str, bytes]:
        """Get card content."""
        return self._content

    @property
    def hash(self) -> str:
        """Get card hash."""
        return self._hash

    @property
    def g_time(self) -> str:
        """Get card global time."""
        return self._g_time.isoformat()

    def _compute_hash(self) -> str:
        """Compute hash for content."""
        hasher = hashlib.sha512()
        if isinstance(self._content, str):
            hasher.update(self._content.encode())
        else:
            hasher.update(self._content)
        return hasher.hexdigest()

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
        content_preview = str(self._content)[:50]
        if len(content_preview) < len(str(self._content)):
            content_preview += "..."
        return f"MCard(hash={self.hash}, g_time={self.g_time}, content={content_preview})"
