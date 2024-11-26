"""Tests for TimeService."""
import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from mcard.domain.models.config import TimeSettings
from mcard.domain.models.exceptions import ValidationError
from mcard.domain.services.time import (
    TimeService, get_time_service, set_time_service,
    get_now_with_located_zone
)

class TestTimeService:
    """Test suite for TimeService."""

    def test_initialization(self, time_settings):
        """Test TimeService initialization."""
        service = TimeService(time_settings)
        assert service.settings == time_settings
        assert service.settings.time_format == TimeSettings.DB_TIME_FORMAT

    def test_initialization_default(self):
        """Test TimeService initialization with default settings."""
        service = TimeService()
        assert service.settings.time_format == TimeSettings.DB_TIME_FORMAT

    def test_get_current_time_utc(self, time_settings):
        """Test getting current time in UTC."""
        service = TimeService(time_settings)
        current = service.get_current_time()
        assert current.tzinfo == timezone.utc

    def test_get_current_time_local(self):
        """Test getting current time in local timezone."""
        settings = TimeSettings(timezone="America/New_York", use_utc=False)
        service = TimeService(settings)
        current = service.get_current_time()
        assert isinstance(current.tzinfo, ZoneInfo)
        assert str(current.tzinfo) == "America/New_York"

    def test_format_time(self, time_settings):
        """Test time formatting."""
        service = TimeService(time_settings)
        test_time = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        formatted = service.format_time(test_time)
        assert "2023-01-01" in formatted
        assert "12:00:00" in formatted
        assert ".123456" in formatted
        assert "+0000" in formatted

    def test_format_time_with_microseconds(self, time_settings):
        """Test time formatting with microseconds."""
        service = TimeService(time_settings)
        test_time = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        formatted = service.format_time(test_time)
        assert ".123456" in formatted

    def test_parse_time(self, time_settings):
        """Test time parsing."""
        service = TimeService(time_settings)
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

    def test_parse_time_with_microseconds(self, time_settings):
        """Test parsing time with microseconds."""
        service = TimeService(time_settings)
        test_str = "2023-01-01 12:00:00.123456 +0000"
        parsed = service.parse_time(test_str)
        assert parsed.microsecond == 123456

    def test_parse_time_utc_formats(self, time_settings):
        """Test parsing various UTC time formats."""
        service = TimeService(time_settings)
        test_str = "2023-01-01 12:00:00.123456 +0000"
        parsed = service.parse_time(test_str)
        assert parsed.tzinfo == timezone.utc

    def test_parse_time_invalid(self, time_settings):
        """Test parsing invalid time string."""
        service = TimeService(time_settings)
        with pytest.raises(ValueError):
            service.parse_time("invalid time string")

    def test_invalid_time_format(self):
        """Test handling invalid time format."""
        with pytest.raises(ValidationError):
            TimeSettings(time_format="invalid format")

    def test_convert_timezone(self, time_settings):
        """Test timezone conversion."""
        service = TimeService(time_settings)
        test_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        ny_tz = ZoneInfo("America/New_York")
        converted = service.convert_timezone(test_time, ny_tz)
        assert converted.tzinfo == ny_tz
        assert converted.hour == 7  # UTC noon is 7 AM in NY

    def test_convert_timezone_invalid(self, time_settings):
        """Test conversion with invalid timezone."""
        service = TimeService(time_settings)
        test_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValidationError):
            service.convert_timezone(test_time, "Invalid/Zone")

    def test_invalid_timezone(self):
        """Test handling invalid timezone."""
        with pytest.raises(ValidationError):
            TimeSettings(timezone="Invalid/Zone")

    def test_create_time_range(self, time_settings):
        """Test creating time range."""
        service = TimeService(time_settings)
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        time_range = service.create_time_range(start, end)
        assert time_range.start == start
        assert time_range.end == end

    def test_is_within_range(self, time_settings):
        """Test time range check."""
        service = TimeService(time_settings)
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
        time_range = service.create_time_range(start, end)
        
        test_time = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        assert service.is_within_range(test_time, time_range)
        
        test_time = datetime(2023, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
        assert not service.is_within_range(test_time, time_range)

    def test_compare_times(self, time_settings):
        """Test time comparison."""
        service = TimeService(time_settings)
        time1 = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        assert service.compare_times(time1, time2) < 0
        assert service.compare_times(time2, time1) > 0
        assert service.compare_times(time1, time1) == 0

    def test_list_available_timezones(self, time_settings):
        """Test listing available timezones."""
        service = TimeService(time_settings)
        timezones = service.list_available_timezones()
        assert isinstance(timezones, list)
        assert len(timezones) > 0
        assert "UTC" in timezones
        assert "America/New_York" in timezones

    def test_get_now_with_located_zone(self):
        """Test getting current time with located zone."""
        # Initialize with UTC settings
        set_time_service(TimeService(TimeSettings(use_utc=True)))
        result = get_now_with_located_zone()
        assert result.tzinfo == timezone.utc
        
        # Test with specific timezone
        set_time_service(TimeService(TimeSettings(timezone="America/New_York", use_utc=False)))
        result = get_now_with_located_zone()
        assert str(result.tzinfo) == "America/New_York"
        
        # Reset to default
        set_time_service(None)
        result = get_now_with_located_zone()
        assert result.tzinfo is not None  # Ensure timezone info is present

    def test_parse_time_missing_timezone(self, time_settings):
        """Test parsing time string without timezone info."""
        service = TimeService(time_settings)
        # Test with UTC settings
        test_str = "2023-01-01 12:00:00"
        parsed = service.parse_time(test_str)
        assert parsed.tzinfo == timezone.utc
        
        # Test with specific timezone
        service = TimeService(TimeSettings(timezone="America/New_York", use_utc=False))
        parsed = service.parse_time(test_str)
        assert str(parsed.tzinfo) == "America/New_York"

    def test_time_range_boundary_conditions(self, time_settings):
        """Test time range boundary conditions."""
        service = TimeService(time_settings)
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
    # Test default service
    service1 = get_time_service()
    assert isinstance(service1, TimeService)

    # Test setting custom service
    custom_settings = TimeSettings(timezone="America/Los_Angeles")
    custom_service = TimeService(custom_settings)
    set_time_service(custom_service)
    
    # Verify custom service is returned
    service2 = get_time_service()
    assert service2 == custom_service
    assert service2.settings == custom_settings
