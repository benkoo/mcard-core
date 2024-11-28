"""Pytest configuration and fixtures."""
import os
import pytest
from datetime import datetime, timezone

@pytest.fixture
def fixed_datetime():
    """Fixture providing a fixed datetime for consistent testing."""
    return datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
