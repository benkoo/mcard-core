"""Pytest configuration and fixtures."""
import os
import pytest
from datetime import datetime, timezone
from mcard.domain.models.config import TimeSettings
from mcard.domain.services.time import TimeService

@pytest.fixture
def time_settings():
    """Fixture for TimeSettings with test configuration."""
    return TimeSettings(
        timezone="UTC",
        time_format=TimeSettings.DB_TIME_FORMAT,  # Use the required database format
        date_format="%Y-%m-%d",
        use_utc=True
    )

@pytest.fixture
def time_service(time_settings):
    """Fixture for TimeService with test configuration."""
    return TimeService(time_settings)

@pytest.fixture
def fixed_datetime():
    """Fixture providing a fixed datetime for consistent testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
