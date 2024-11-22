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
        # Create and save MCard
        card = MCard(
            content=self.text_content,
            content_hash=self.text_hash,
            time_claimed=datetime.now(timezone.utc)
        )
        self.storage.save(card)

        # Retrieve and verify
        retrieved = self.storage.get(self.text_hash)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, self.text_content)
        self.assertEqual(retrieved.content_hash, self.text_hash)
        self.assertEqual(retrieved.time_claimed.tzinfo, timezone.utc)

    def test_save_and_get_binary(self):
        """Test saving and retrieving binary content."""
        # Create and save MCard
        card = MCard(
            content=self.binary_content,
            content_hash=self.binary_hash,
            time_claimed=datetime.now(timezone.utc)
        )
        self.storage.save(card)

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
        self.storage.save(card)

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
        for card in cards:
            self.storage.save(card)

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
        self.storage.save(card)

        # Verify it exists
        self.assertIsNotNone(self.storage.get(self.text_hash))

        # Delete and verify
        self.assertTrue(self.storage.delete(self.text_hash))
        self.assertIsNone(self.storage.get(self.text_hash))

        # Try deleting non-existent card
        self.assertFalse(self.storage.delete("nonexistent"))

    def test_update_existing(self):
        """Test updating an existing MCard."""
        # Create and save initial MCard
        initial_time = datetime.now(timezone.utc)
        card = MCard(
            content=self.text_content,
            content_hash=self.text_hash,
            time_claimed=initial_time
        )
        self.storage.save(card)

        # Update with new time
        new_time = datetime.now(timezone.utc)
        updated_card = MCard(
            content=self.text_content,
            content_hash=self.text_hash,
            time_claimed=new_time
        )
        self.storage.save(updated_card)

        # Retrieve and verify
        retrieved = self.storage.get(self.text_hash)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.time_claimed, new_time)


if __name__ == '__main__':
    unittest.main()
