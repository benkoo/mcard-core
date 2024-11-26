"""
Time service for handling time-related operations.
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, available_timezones
from dataclasses import dataclass

@dataclass
class TimeRange:
    """Time range with start and end times."""
    start: datetime
    end: datetime

class TimeService:
    """Service for handling time-related operations."""
    
    def get_current_time(self) -> datetime:
        """Get current time in UTC."""
        return datetime.now(timezone.utc)

    def format_time(self, dt: datetime, use_date_format: bool = False) -> str:
        """Format datetime according to standard format."""
        fmt = "%Y-%m-%d" if use_date_format else "%Y-%m-%d %H:%M:%S.%f %z"
        return dt.strftime(fmt)

    def parse_time(self, time_str: str) -> datetime:
        """Parse time string according to standard format."""
        try:
            # First try parsing with the standard format
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f %z")
        except ValueError:
            # If that fails, try a few common formats
            common_formats = [
                "%Y-%m-%d %H:%M:%S %z",     # Standard format with offset
                "%Y-%m-%d %H:%M:%S.%f",     # Format without timezone
                "%Y-%m-%d %H:%M:%S",        # Basic format without microseconds
                "%Y-%m-%d",                 # Basic date format
            ]
            
            for fmt in common_formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Could not parse time string: {time_str}")

        # If no timezone info, use UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def convert_timezone(self, dt: datetime, target_tz: str | ZoneInfo) -> datetime:
        """Convert datetime to target timezone."""
        if isinstance(target_tz, str):
            try:
                target_tz = ZoneInfo(target_tz)
            except Exception as e:
                raise ValueError(f"Invalid timezone: {target_tz}")
        return dt.astimezone(target_tz)

    def create_time_range(self, start: datetime, end: datetime) -> TimeRange:
        """Create a time range between start and end times."""
        return TimeRange(start=start, end=end)

    def is_within_range(self, dt: datetime, time_range: TimeRange) -> bool:
        """Check if datetime is within the given time range."""
        return time_range.start <= dt <= time_range.end

    def compare_times(self, dt1: datetime, dt2: datetime) -> int:
        """Compare two datetimes, returns -1 if dt1 < dt2, 0 if equal, 1 if dt1 > dt2."""
        if dt1 < dt2:
            return -1
        elif dt1 > dt2:
            return 1
        return 0

    def list_available_timezones(self) -> list[str]:
        """List all available timezones."""
        return sorted(available_timezones())

# Global time service instance
_time_service: TimeService | None = None

def get_time_service() -> TimeService:
    """Get the global time service instance."""
    global _time_service
    if _time_service is None:
        _time_service = TimeService()
    return _time_service

def set_time_service(service: TimeService | None) -> None:
    """Set the global time service instance."""
    global _time_service
    _time_service = service

def get_now_with_located_zone() -> datetime:
    """Get current time with UTC timezone."""
    return get_time_service().get_current_time()

def format_time(dt: datetime, use_date_format: bool = False) -> str:
    """Format datetime according to standard format."""
    return get_time_service().format_time(dt, use_date_format)

def parse_time(time_str: str) -> datetime:
    """Parse time string according to standard format."""
    return get_time_service().parse_time(time_str)

def convert_timezone(dt: datetime, target_tz: str) -> datetime:
    """Convert datetime to target timezone."""
    return get_time_service().convert_timezone(dt, target_tz)

def create_time_range(start: datetime, end: datetime) -> TimeRange:
    """Create a time range between start and end times."""
    return get_time_service().create_time_range(start, end)

def is_within_range(dt: datetime, time_range: TimeRange) -> bool:
    """Check if datetime is within the given time range."""
    return get_time_service().is_within_range(dt, time_range)

def compare_times(dt1: datetime, dt2: datetime) -> int:
    """Compare two datetimes, returns -1 if dt1 < dt2, 0 if equal, 1 if dt1 > dt2."""
    return get_time_service().compare_times(dt1, dt2)

def list_available_timezones() -> list[str]:
    """List all available timezones."""
    return get_time_service().list_available_timezones()
