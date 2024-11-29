"""Time-related domain services."""
from datetime import datetime, timezone

def get_now_with_located_zone() -> datetime:
    """Get current time with timezone information."""
    return datetime.now(timezone.utc)
