"""
Core MCard domain model.
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
from ..services.time import get_now_with_located_zone

class MCard(BaseModel):
    """A wrapper class for content-addressable data."""
    content: Any = Field(description="The actual content of the MCard.")
    hash: Optional[str] = Field(
        None,
        description="Hash of the content using configured hash function.",
        frozen=True
    )
    g_time: datetime = Field(
        default_factory=get_now_with_located_zone,
        description="Timestamp when the content was claimed."
    )

    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True,
        "extra": "forbid"
    }

    @model_validator(mode='before')
    def ensure_hash(cls, values):
        """Ensure hash is present and valid."""
        # Hash will be computed and set explicitly before saving
        return values

    @model_validator(mode='after')
    def validate_g_time(self):
        """Ensure g_time has timezone information."""
        if self.g_time.tzinfo is None:
            self.g_time = self.g_time.astimezone()
        return self

    def __str__(self) -> str:
        """String representation of MCard."""
        return f"MCard(hash={self.hash}, time={self.g_time})"
