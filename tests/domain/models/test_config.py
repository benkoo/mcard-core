"""Tests for configuration models."""
import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
from mcard.domain.models.config import TimeSettings, AppSettings, DatabaseSettings
from mcard.domain.models.exceptions import ValidationError

def test_time_settings_defaults():
    """Test default values for TimeSettings."""
    settings = TimeSettings()
    assert settings.timezone is None
    assert settings.time_format == TimeSettings.DB_TIME_FORMAT
    assert settings.date_format == "%Y-%m-%d"
    assert settings.use_utc is False

def test_time_settings_custom():
    """Test custom values for TimeSettings."""
    settings = TimeSettings(
        timezone="America/New_York",
        time_format=TimeSettings.DB_TIME_FORMAT,  # Must use DB format
        date_format="%Y-%m-%d",
        use_utc=True
    )
    assert settings.timezone == "America/New_York"
    assert settings.time_format == TimeSettings.DB_TIME_FORMAT
    assert settings.date_format == "%Y-%m-%d"
    assert settings.use_utc is True

def test_time_settings_validate_timezone():
    """Test timezone validation."""
    # Valid timezone
    settings = TimeSettings(timezone="America/New_York")
    assert settings.timezone == "America/New_York"

    # Invalid timezone
    with pytest.raises(ValidationError, match=r"Invalid timezone.*"):
        TimeSettings(timezone="Invalid/Zone")

def test_time_settings_validate_format():
    """Test time format validation."""
    # Only DB format is allowed for time_format
    with pytest.raises(ValidationError, match=r"Time format must be.*"):
        TimeSettings(time_format="%Y-%m-%d %H:%M:%S")

    # Valid date formats
    valid_date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%m-%Y",
    ]
    for fmt in valid_date_formats:
        settings = TimeSettings(date_format=fmt)
        assert settings.date_format == fmt

    # Invalid date formats
    invalid_date_formats = [
        "invalid format",
        "%Y-%m-%d %invalid",
        "%Y-%m-%d %%",
    ]
    for fmt in invalid_date_formats:
        with pytest.raises(ValidationError, match=r"Invalid format string.*"):
            TimeSettings(date_format=fmt)

def test_time_settings_microseconds():
    """Test microseconds handling."""
    settings = TimeSettings()
    assert "%f" in settings.time_format  # Ensure microseconds are included

def test_time_settings_timezone_precedence():
    """Test timezone precedence."""
    settings = TimeSettings(timezone="America/New_York", use_utc=True)
    assert settings.timezone == "America/New_York"
    assert settings.use_utc is True

def test_time_settings_format_compatibility():
    """Test format compatibility with datetime."""
    settings = TimeSettings()
    now = datetime.now(ZoneInfo("UTC"))
    # Should not raise an error
    now.strftime(settings.time_format)
    now.strftime(settings.date_format)

class TestTimeSettings:
    """Test suite for TimeSettings."""

    def test_default_values(self):
        """Test TimeSettings with default values."""
        settings = TimeSettings()
        assert settings.timezone is None
        assert settings.time_format == TimeSettings.DB_TIME_FORMAT
        assert settings.date_format == "%Y-%m-%d"
        assert settings.use_utc is False

    def test_custom_values(self):
        """Test TimeSettings with custom values."""
        settings = TimeSettings(
            timezone="America/New_York",
            time_format=TimeSettings.DB_TIME_FORMAT,  # Must use DB format
            date_format="%Y-%m-%d",
            use_utc=True
        )
        assert settings.timezone == "America/New_York"
        assert settings.time_format == TimeSettings.DB_TIME_FORMAT
        assert settings.date_format == "%Y-%m-%d"
        assert settings.use_utc is True

    def test_invalid_timezone(self):
        """Test TimeSettings with invalid timezone."""
        with pytest.raises(ValidationError, match=r"Invalid timezone.*"):
            TimeSettings(timezone="Invalid/Timezone")

    def test_invalid_time_format(self):
        """Test TimeSettings with invalid time format."""
        with pytest.raises(ValidationError, match=r"Time format must be.*"):
            TimeSettings(time_format="invalid format")

    def test_invalid_date_format(self):
        """Test TimeSettings with invalid date format."""
        with pytest.raises(ValidationError, match=r"Invalid format string.*"):
            TimeSettings(date_format="invalid format")

class TestAppSettings:
    """Test suite for AppSettings."""

    def test_default_values(self):
        """Test AppSettings with default values."""
        settings = AppSettings(database=DatabaseSettings(db_path="test.db"))
        assert isinstance(settings.time, TimeSettings)
        assert settings.time == TimeSettings()

    def test_custom_time_settings(self):
        """Test AppSettings with custom TimeSettings."""
        time_settings = TimeSettings(
            timezone="UTC",
            use_utc=True
        )
        settings = AppSettings(
            database=DatabaseSettings(db_path="test.db"),
            time=time_settings
        )
        assert settings.time == time_settings

    def test_from_environment(self, monkeypatch):
        """Test AppSettings configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("MCARD_DATABASE__DB_PATH", "test.db")
        monkeypatch.setenv("MCARD_TIME__TIMEZONE", "America/Los_Angeles")
        monkeypatch.setenv("MCARD_TIME__TIME_FORMAT", TimeSettings.DB_TIME_FORMAT)
        monkeypatch.setenv("MCARD_TIME__DATE_FORMAT", "%d/%m/%Y")
        monkeypatch.setenv("MCARD_TIME__USE_UTC", "true")

        # Create settings from environment
        settings = AppSettings()
        assert settings.time.timezone == "America/Los_Angeles"
        assert settings.time.time_format == TimeSettings.DB_TIME_FORMAT
        assert settings.time.date_format == "%d/%m/%Y"
        assert settings.time.use_utc is True

    def test_invalid_environment_values(self, monkeypatch):
        """Test AppSettings with invalid environment values."""
        monkeypatch.setenv("MCARD_DATABASE__DB_PATH", "test.db")
        monkeypatch.setenv("MCARD_TIME__TIMEZONE", "Invalid/Timezone")
        
        with pytest.raises(ValidationError):
            AppSettings()
