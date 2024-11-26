"""
Time service for handling time-related operations.
"""
from typing import Optional, Tuple, Union, List
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones
from ..models.config import TimeSettings
from ..models.exceptions import ValidationError
from dataclasses import dataclass

class TimeService:
    """Service for handling time-related operations."""

    def __init__(self, settings: Optional[TimeSettings] = None):
        """Initialize TimeService with settings."""
        self.settings = settings or TimeSettings()

    def get_current_time(self) -> datetime:
        """Get current time with timezone."""
        if self.settings.use_utc:
            return datetime.now(timezone.utc)
        elif self.settings.timezone:
            return datetime.now(ZoneInfo(self.settings.timezone))
        else:
            # Default to UTC if no timezone specified
            return datetime.now(timezone.utc)

    def format_time(self, dt: datetime, use_date_format: bool = False) -> str:
        """Format datetime according to settings."""
        fmt = self.settings.date_format if use_date_format else self.settings.time_format
        return dt.strftime(fmt)

    def parse_time(self, time_str: str) -> datetime:
        """Parse time string according to settings."""
        try:
            # First try parsing with the configured format
            return datetime.strptime(time_str, self.settings.time_format)
        except ValueError:
            # If that fails, try a few common formats
            common_formats = [
                "%Y-%m-%d %H:%M:%S.%f %z",  # Standard format with microseconds and offset
                "%Y-%m-%d %H:%M:%S %z",     # Standard format with offset
                "%Y-%m-%d %H:%M:%S.%f",     # Format without timezone
                "%Y-%m-%d %H:%M:%S",        # Basic format
            ]
            
            for fmt in common_formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    if dt.tzinfo is None:
                        # If no timezone info, use UTC or configured timezone
                        tz = timezone.utc if self.settings.use_utc else (
                            ZoneInfo(self.settings.timezone) if self.settings.timezone else timezone.utc
                        )
                        dt = dt.replace(tzinfo=tz)
                    return dt
                except ValueError:
                    continue
            
            raise ValueError(f"Could not parse time string: {time_str}")

    def convert_timezone(self, dt: datetime, target_tz: Union[str, ZoneInfo]) -> datetime:
        """Convert datetime to target timezone."""
        if isinstance(target_tz, str):
            try:
                target_tz = ZoneInfo(target_tz)
            except Exception as e:
                raise ValidationError(f"Invalid timezone: {target_tz}")
        return dt.astimezone(target_tz)

    def create_time_range(self, start: datetime, end: datetime) -> 'TimeRange':
        """Create a time range between start and end times."""
        return TimeRange(start=start, end=end)

    def is_within_range(self, dt: datetime, time_range: 'TimeRange') -> bool:
        """Check if datetime is within the given time range."""
        return time_range.start <= dt <= time_range.end

    def compare_times(self, dt1: datetime, dt2: datetime) -> int:
        """Compare two datetimes, returns -1 if dt1 < dt2, 0 if equal, 1 if dt1 > dt2."""
        if dt1 < dt2:
            return -1
        elif dt1 > dt2:
            return 1
        return 0

    def list_available_timezones(self) -> List[str]:
        """List all available timezones."""
        return sorted(available_timezones())

@dataclass
class TimeRange:
    start: datetime
    end: datetime

# Global instance
_default_service = None

def get_time_service() -> TimeService:
    """Get the global time service instance."""
    global _default_service
    if _default_service is None:
        _default_service = TimeService()
    return _default_service

def set_time_service(service: TimeService) -> None:
    """Set the global time service instance."""
    global _default_service
    _default_service = service

def get_now_with_located_zone() -> datetime:
    """
    Get current time with the local timezone.
    Always ensures timezone information is present.
    Returns time with configured timezone.
    """
    return get_time_service().get_current_time()
