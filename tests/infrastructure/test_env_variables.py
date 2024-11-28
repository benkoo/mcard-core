import os
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def test_mcard_api_key_from_env():
    """Test if MCARD_API_KEY is correctly loaded from the .env file."""
    expected_api_key = 'test_api_key'
    actual_api_key = os.getenv('MCARD_API_KEY')
    assert actual_api_key == expected_api_key, f"Expected MCARD_API_KEY to be '{expected_api_key}', but got '{actual_api_key}'"


def test_mcard_api_key_not_set():
    """Test behavior when MCARD_API_KEY is not set in the environment."""
    # Temporarily unset the MCARD_API_KEY
    os.environ.pop('MCARD_API_KEY', None)
    actual_api_key = os.getenv('MCARD_API_KEY')
    assert actual_api_key is None, "Expected MCARD_API_KEY to be None when not set, but it was not."
