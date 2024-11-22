"""Test cases for MCard storage."""
import os
import unittest
from datetime import datetime, timezone
from mcard.core import MCard
from mcard.storage import MCardStorage

class TestMCardStorage(unittest.TestCase):
    """Test cases for MCardStorage."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_db = "test_mcards.db"
        self.storage = MCardStorage(self.test_db)
        
        # Test data
        self.text_content = "Hello World"
        self.text_hash = "6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba"
        self.binary_content = b"Binary Data"
        self.binary_hash = "4d6f7c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c4c"
        self.number_content = 12345
        self.number_hash = "5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5"

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_save_and_get_text(self):
        """Test saving and retrieving text content."""
        # Create and save MCard with local timezone
        local_time = datetime.now().astimezone()
        card = MCard(
            content=self.text_content,
            content_hash=self.text_hash,
            time_claimed=local_time
        )
        result = self.storage.save(card)
        self.assertTrue(result)  # Should return True for new record

        # Retrieve and verify
        retrieved = self.storage.get(self.text_hash)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, self.text_content)
        self.assertEqual(retrieved.content_hash, self.text_hash)
        # Time should preserve original timezone
        self.assertEqual(retrieved.time_claimed.tzinfo, local_time.tzinfo)
        self.assertEqual(retrieved.time_claimed.timestamp(), local_time.timestamp())

    def test_save_duplicate(self):
        """Test that saving a duplicate record returns False and doesn't update."""
        # Create and save initial MCard
        initial_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        card1 = MCard(
            content=self.text_content,
            content_hash=self.text_hash,
            time_claimed=initial_time
        )
        result1 = self.storage.save(card1)
        self.assertTrue(result1)  # Should return True for new record

        # Try to save another MCard with same hash but different time
        new_time = datetime(2024, 2, 1, tzinfo=timezone.utc)
        card2 = MCard(
            content=self.text_content,
            content_hash=self.text_hash,
            time_claimed=new_time
        )
        result2 = self.storage.save(card2)
        self.assertFalse(result2)  # Should return False for duplicate

        # Verify the original record wasn't updated
        retrieved = self.storage.get(self.text_hash)
        self.assertEqual(retrieved.time_claimed, initial_time)

    def test_save_many(self):
        """Test saving multiple records at once."""
        # Create test cards
        cards = [
            MCard(content="Card 1", content_hash="1" * 64),
            MCard(content="Card 2", content_hash="2" * 64),
            MCard(content="Card 3", content_hash="3" * 64)
        ]
        
        # Save all cards
        saved, skipped = self.storage.save_many(cards)
        self.assertEqual(saved, 3)
        self.assertEqual(skipped, 0)
        
        # Try saving some duplicates
        more_cards = [
            MCard(content="Card 1", content_hash="1" * 64),  # Duplicate
            MCard(content="Card 4", content_hash="4" * 64),  # New
            MCard(content="Card 2", content_hash="2" * 64)   # Duplicate
        ]
        saved, skipped = self.storage.save_many(more_cards)
        self.assertEqual(saved, 1)    # Only Card 4 should be saved
        self.assertEqual(skipped, 2)  # Card 1 and 2 should be skipped
        
        # Verify total number of records
        all_cards = self.storage.get_all()
        self.assertEqual(len(all_cards), 4)

    def test_save_and_get_binary(self):
        """Test saving and retrieving binary content."""
        # Create and save MCard
        card = MCard(
            content=self.binary_content,
            content_hash=self.binary_hash,
            time_claimed=datetime.now(timezone.utc)
        )
        result = self.storage.save(card)
        self.assertTrue(result)

        # Retrieve and verify
        retrieved = self.storage.get(self.binary_hash)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, self.binary_content)
        self.assertEqual(retrieved.content_hash, self.binary_hash)

    def test_save_and_get_number(self):
        """Test saving and retrieving numeric content."""
        # Create and save MCard
        card = MCard(
            content=self.number_content,
            content_hash=self.number_hash,
            time_claimed=datetime.now(timezone.utc)
        )
        result = self.storage.save(card)
        self.assertTrue(result)

        # Retrieve and verify
        retrieved = self.storage.get(self.number_hash)
        self.assertIsNotNone(retrieved)
        self.assertEqual(int(retrieved.content), self.number_content)
        self.assertEqual(retrieved.content_hash, self.number_hash)

    def test_get_all(self):
        """Test retrieving all stored MCards."""
        # Create and save multiple MCards
        cards = [
            MCard(content=self.text_content, content_hash=self.text_hash),
            MCard(content=self.binary_content, content_hash=self.binary_hash),
            MCard(content=self.number_content, content_hash=self.number_hash)
        ]
        saved, skipped = self.storage.save_many(cards)
        self.assertEqual(saved, 3)
        self.assertEqual(skipped, 0)

        # Retrieve all and verify
        retrieved = self.storage.get_all()
        self.assertEqual(len(retrieved), 3)
        hashes = {card.content_hash for card in retrieved}
        self.assertEqual(
            hashes,
            {self.text_hash, self.binary_hash, self.number_hash}
        )

    def test_delete(self):
        """Test deleting MCards."""
        # Create and save MCard
        card = MCard(
            content=self.text_content,
            content_hash=self.text_hash
        )
        result = self.storage.save(card)
        self.assertTrue(result)

        # Verify it exists
        self.assertIsNotNone(self.storage.get(self.text_hash))

        # Delete and verify
        deleted = self.storage.delete(self.text_hash)
        self.assertTrue(deleted)
        self.assertIsNone(self.storage.get(self.text_hash))

        # Try deleting again
        deleted = self.storage.delete(self.text_hash)
        self.assertFalse(deleted)

if __name__ == '__main__':
    unittest.main()
