"""
MCard: A wrapper class for content-addressable data.
"""
from datetime import datetime, timezone, timedelta
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import hashlib
import time


def get_now_with_located_zone() -> datetime:
    """
    Get current time with the local timezone. Falls back to UTC if local timezone
    cannot be determined.
    """
    current_time = datetime.now()
    if current_time.tzinfo is None:
        try:
            current_time = current_time.astimezone()
        except Exception:
            # Fallback to UTC
            current_time = current_time.replace(tzinfo=timezone.utc)
    return current_time


class MCard(BaseModel):
    """
    A wrapper class for content-addressable data.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='forbid'
    )

    content: Any = Field(description="The actual content of the MCard.")
    content_hash: str = Field(description="SHA-256 hash of the content.", default=None)
    time_claimed: datetime = Field(
        default_factory=get_now_with_located_zone,
        description="Timestamp when the content was claimed."
    )

    @model_validator(mode='before')
    def calculate_content_hash(cls, values):
        """Calculate content hash if not provided."""
        if 'content' in values and ('content_hash' not in values or values['content_hash'] is None):
            content = values['content']
            if isinstance(content, str):
                content = content.encode('utf-8')
            elif not isinstance(content, bytes):
                content = str(content).encode('utf-8')
            values['content_hash'] = hashlib.sha256(content).hexdigest()
        return values

    @field_validator('content_hash')
    def validate_content_hash(cls, v: str) -> str:
        """Validate content_hash format."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("content_hash must be a string")
        if len(v) != 64:
            raise ValueError("content_hash must be a 64-character hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("content_hash must be a valid hex string")
        return v.lower()

    @field_validator('time_claimed')
    def validate_time_claimed(cls, v: datetime) -> datetime:
        """Ensure time_claimed has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    def __str__(self) -> str:
        """String representation of MCard."""
        return f"MCard(content_hash={self.content_hash})"
