"""Tests for the MCard class."""
import unittest
from datetime import datetime, timezone, timedelta
from mcard.core import MCard
import hashlib


class TestMCard(unittest.TestCase):
    """Test cases for the MCard class."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_content = "Hello World"
        self.valid_hash = "6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba"

    def test_create_mcard_with_valid_data(self):
        """Test creating an MCard with valid data."""
        content = "test content"
        mcard = MCard(content=content)
        self.assertEqual(mcard.content, content)
        self.assertEqual(len(mcard.content_hash), 64)  # SHA-256 hash is 64 chars
        self.assertIsNotNone(mcard.time_claimed)
        self.assertIsNotNone(mcard.time_claimed.tzinfo)

    def test_content_hash_validation(self):
        """Test content hash validation."""
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

        # Test that content_hash is automatically calculated
        content = "test content"
        mcard = MCard(content=content)
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        self.assertEqual(mcard.content_hash, expected_hash)

        # Test that content_hash cannot be manually set
        with self.assertRaises(ValueError):
            mcard = MCard(content="test", content_hash="invalid")

        # Test that content_hash cannot be modified after creation
        mcard = MCard(content="test")
        with self.assertRaises(ValueError):
            mcard.content_hash = "something else"

    def test_different_content_types(self):
        """Test that content_hash is correctly calculated for different content types."""
        # Test with string
        mcard_str = MCard(content="test")
        self.assertEqual(mcard_str.content_hash, hashlib.sha256("test".encode('utf-8')).hexdigest())

        # Test with number
        mcard_num = MCard(content=42)
        self.assertEqual(mcard_num.content_hash, hashlib.sha256("42".encode('utf-8')).hexdigest())

        # Test with dict
        content_dict = {"key": "value"}
        mcard_dict = MCard(content=content_dict)
        self.assertEqual(mcard_dict.content_hash, hashlib.sha256(str(content_dict).encode('utf-8')).hexdigest())

        # Test with bytes
        content_bytes = b"test bytes"
        mcard_bytes = MCard(content=content_bytes)
        self.assertEqual(mcard_bytes.content_hash, hashlib.sha256(content_bytes).hexdigest())

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
