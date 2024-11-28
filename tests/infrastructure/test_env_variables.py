import os
import pytest
from dotenv import load_dotenv
from pathlib import Path

# Load test-specific environment variables
test_env_path = Path(__file__).parent.parent / '.env.test'
load_dotenv(test_env_path, override=True)  # Add override=True to ensure test values take precedence


def test_mcard_api_key_from_env():
    """Test if MCARD_API_KEY is correctly loaded from the .env file."""
    expected_api_key = 'test_custom_api_key_12345'  # Match the API key used in other tests
    actual_api_key = os.getenv('MCARD_API_KEY')
    assert actual_api_key == expected_api_key, f"Expected MCARD_API_KEY to be '{expected_api_key}', but got '{actual_api_key}'"


def test_mcard_api_key_not_set():
    """Test behavior when MCARD_API_KEY is not set."""
    # Temporarily remove MCARD_API_KEY from environment
    original_key = os.environ.pop('MCARD_API_KEY', None)
    try:
        assert os.getenv('MCARD_API_KEY') is None
    finally:
        # Restore original API key
        if original_key is not None:
            os.environ['MCARD_API_KEY'] = original_key
