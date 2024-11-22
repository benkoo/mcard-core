"""Tests for the MCard class."""
import unittest
from datetime import datetime, timezone, timedelta
from mcard.core import MCard


class TestMCard(unittest.TestCase):
    """Test cases for the MCard class."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_content = "Hello World"
        self.valid_hash = "6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba"

    def test_create_mcard_with_valid_data(self):
        """Test creating an MCard with valid data."""
        card = MCard(
            content=self.valid_content,
            content_hash=self.valid_hash
        )
        self.assertEqual(card.content, self.valid_content)
        self.assertEqual(card.content_hash, self.valid_hash)
        self.assertIsNotNone(card.time_claimed)
        self.assertIsNotNone(card.time_claimed.tzinfo)

    def test_content_hash_validation(self):
        """Test content_hash validation."""
        # Test invalid hash length
        with self.assertRaises(ValueError):
            MCard(
                content=self.valid_content,
                content_hash="abc123"
            )

        # Test invalid characters
        with self.assertRaises(ValueError):
            MCard(
                content=self.valid_content,
                content_hash="x" * 64
            )

        # Test hash normalization
        card = MCard(
            content=self.valid_content,
            content_hash=self.valid_hash.upper()
        )
        self.assertEqual(card.content_hash, self.valid_hash.lower())

    def test_time_claimed_timezone(self):
        """Test time_claimed timezone handling."""
        # Test auto-generation of time_claimed
        card = MCard(
            content=self.valid_content,
            content_hash=self.valid_hash
        )
        self.assertIsNotNone(card.time_claimed.tzinfo)

        # Test custom timezone
        utc_dt = datetime.now(timezone.utc)
        card = MCard(
            content=self.valid_content,
            content_hash=self.valid_hash,
            time_claimed=utc_dt
        )
        self.assertEqual(card.time_claimed.tzinfo, timezone.utc)


if __name__ == '__main__':
    unittest.main()
