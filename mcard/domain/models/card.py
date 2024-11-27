"""
Core MCard domain model.
"""
from datetime import datetime
import hashlib

class MCard:
    """A class representing a content-addressable data structure."""

    def __init__(self, content, hash=None, g_time=None):
        self._content = content
        self._hash = hash if hash is not None else self.compute_hash(content)
        self._g_time = g_time if g_time is not None else self.get_current_time()

    @property
    def content(self):
        return self._content

    @property
    def hash(self):
        return self._hash

    @property
    def g_time(self):
        return self._g_time

    def compute_hash(self, content):
        """Compute the SHA-256 hash of the content."""
        content_bytes = content.encode() if isinstance(content, str) else content
        return hashlib.sha256(content_bytes).hexdigest()

    def get_current_time(self):
        """Get the current time as a string with microsecond precision."""
        return datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S.%f %Z')

    def __str__(self):
        """String representation of MCard."""
        return f"MCard(hash={self.hash}, g_time={self.g_time})"
