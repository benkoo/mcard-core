"""Tests for file-based configuration."""
import os
from pathlib import Path
from mcard.infrastructure.config import get_project_root

def test_env_file_exists():
    """Test that .env file exists in the project root."""
    project_root = get_project_root()
    env_file = project_root / ".env"
    assert env_file.exists(), ".env file not found in project root"

def test_env_test_file_exists():
    """Test that tests/.env.test file exists."""
    project_root = get_project_root()
    test_env_file = project_root / "tests" / ".env.test"
    assert test_env_file.exists(), ".env.test file not found in tests directory"
