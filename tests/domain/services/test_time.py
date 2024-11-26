"""Tests for TimeService."""
import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from mcard.domain.services.time import (
    TimeService, get_time_service, set_time_service,
    get_now_with_located_zone
)

class TestTimeService:
    """Test suite for TimeService."""

    def test_initialization(self):
        """Test TimeService initialization."""
        service = TimeService()
        assert service is not None

    def test_get_current_time_utc(self):
        """Test getting current time in UTC."""
        service = TimeService()
        current = service.get_current_time()
        assert current.tzinfo == timezone.utc

    def test_format_time(self):
        """Test time formatting."""
        service = TimeService()
        test_time = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        formatted = service.format_time(test_time)
        assert "2023-01-01" in formatted
        assert "12:00:00" in formatted
        assert ".123456" in formatted
        assert "+0000" in formatted

    def test_format_time_with_microseconds(self):
        """Test time formatting with microseconds."""
        service = TimeService()
        test_time = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        formatted = service.format_time(test_time)
        assert ".123456" in formatted

    def test_parse_time(self):
        """Test time parsing."""
        service = TimeService()
        test_str = "2023-01-01 12:00:00.123456 +0000"
        parsed = service.parse_time(test_str)
        assert parsed.year == 2023
        assert parsed.month == 1
        assert parsed.day == 1
        assert parsed.hour == 12
        assert parsed.minute == 0
        assert parsed.second == 0
        assert parsed.microsecond == 123456
        assert parsed.tzinfo == timezone.utc

    def test_parse_time_with_microseconds(self):
        """Test parsing time with microseconds."""
        service = TimeService()
        test_str = "2023-01-01 12:00:00.123456 +0000"
        parsed = service.parse_time(test_str)
        assert parsed.microsecond == 123456

    def test_parse_time_utc_formats(self):
        """Test parsing various UTC time formats."""
        service = TimeService()
        test_str = "2023-01-01 12:00:00.123456 +0000"
        parsed = service.parse_time(test_str)
        assert parsed.tzinfo == timezone.utc

    def test_parse_time_invalid(self):
        """Test parsing invalid time string."""
        service = TimeService()
        with pytest.raises(ValueError):
            service.parse_time("invalid time string")

    def test_convert_timezone(self):
        """Test timezone conversion."""
        service = TimeService()
        test_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        ny_tz = ZoneInfo("America/New_York")
        converted = service.convert_timezone(test_time, ny_tz)
        assert converted.tzinfo == ny_tz
        assert converted.hour == 7  # UTC noon is 7 AM in NY

    def test_convert_timezone_invalid(self):
        """Test conversion with invalid timezone."""
        service = TimeService()
        test_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            service.convert_timezone(test_time, "Invalid/Zone")

    def test_create_time_range(self):
        """Test creating time range."""
        service = TimeService()
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        time_range = service.create_time_range(start, end)
        assert time_range.start == start
        assert time_range.end == end

    def test_is_within_range(self):
        """Test time range check."""
        service = TimeService()
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
        time_range = service.create_time_range(start, end)
        
        test_time = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        assert service.is_within_range(test_time, time_range)
        
        test_time = datetime(2023, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
        assert not service.is_within_range(test_time, time_range)

    def test_compare_times(self):
        """Test time comparison."""
        service = TimeService()
        time1 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        assert service.compare_times(time1, time2) < 0
        assert service.compare_times(time2, time1) > 0
        assert service.compare_times(time1, time1) == 0

    def test_list_available_timezones(self):
        """Test listing available timezones."""
        service = TimeService()
        timezones = service.list_available_timezones()
        assert isinstance(timezones, list)
        assert len(timezones) > 0
        assert "UTC" in timezones
        assert "America/New_York" in timezones

    def test_get_now_with_located_zone(self):
        """Test getting current time with located zone."""
        # Initialize with UTC settings
        set_time_service(TimeService())
        result = get_now_with_located_zone()
        assert result.tzinfo == timezone.utc
        
        # Test with specific timezone
        set_time_service(TimeService())
        result = get_now_with_located_zone()
        assert result.tzinfo is not None  # Ensure timezone info is present

    def test_parse_time_missing_timezone(self):
        """Test parsing time string without timezone info."""
        service = TimeService()
        # Test with UTC settings
        test_str = "2023-01-01 12:00:00"
        parsed = service.parse_time(test_str)
        assert parsed.tzinfo == timezone.utc
        
        # Test with specific timezone
        service = TimeService()
        parsed = service.parse_time(test_str)
        assert parsed.tzinfo == timezone.utc

    def test_time_range_boundary_conditions(self):
        """Test time range boundary conditions."""
        service = TimeService()
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
        time_range = service.create_time_range(start, end)
        
        # Test exact boundary times
        assert service.is_within_range(start, time_range)  # Start time should be included
        assert service.is_within_range(end, time_range)    # End time should be included
        
        # Test just outside boundaries
        before = start - timedelta(microseconds=1)
        after = end + timedelta(microseconds=1)
        assert not service.is_within_range(before, time_range)
        assert not service.is_within_range(after, time_range)

def test_global_time_service():
    """Test global time service management."""
    original = get_time_service()
    try:
        new_service = TimeService()
        set_time_service(new_service)
        assert get_time_service() is new_service
    finally:
        set_time_service(original)
