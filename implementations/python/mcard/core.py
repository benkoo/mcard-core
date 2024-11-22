"""
MCard: A wrapper class for content-addressable data.
"""
from datetime import datetime, timezone, timedelta
from typing import Any
from pydantic import BaseModel, Field, field_validator
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
    content: Any = Field(description="The actual content of the MCard.")
    content_hash: str = Field(description="SHA-256 hash of the content.")
    time_claimed: datetime = Field(
        default_factory=get_now_with_located_zone,
        description="Timestamp when the content was claimed."
    )

    @field_validator('content_hash')
    def validate_content_hash(cls, v: str) -> str:
        """Validate content_hash format."""
        if not isinstance(v, str):
            raise ValueError("content_hash must be a string")
        if len(v) != 64:
            raise ValueError("content_hash must be 64 characters long")
        if not all(c in '0123456789abcdefABCDEF' for c in v):
            raise ValueError("content_hash must contain only hexadecimal characters")
        return v.lower()

    @field_validator('time_claimed')
    def validate_time_claimed(cls, v: datetime) -> datetime:
        """Validate time_claimed timezone."""
        if v.tzinfo is None:
            try:
                return v.astimezone()
            except Exception:
                # Fallback to UTC
                return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "content": "Actual MCard Content in English language with actual content_hash value.",
                "content_hash": "6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba",
                "time_claimed": "2024-01-01T12:00:00Z"
            }
        }
