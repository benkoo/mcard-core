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
        if values.get('hash') is None:
            from ..services.hashing import get_hashing_service
            content = values.get('content')
            if content is not None:
                hashing_service = get_hashing_service()
                if isinstance(content, str):
                    content = content.encode('utf-8')
                elif not isinstance(content, bytes):
                    content = str(content).encode('utf-8')
                values['hash'] = hashing_service.hash_content(content)
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
