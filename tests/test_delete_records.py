"""Test cases for deleting records from MCard databases."""
import os
import unittest
import time
from pathlib import Path
from datetime import datetime, timezone
import dotenv
from mcard.core import MCard
from mcard.storage import MCardStorage

class TestDeleteRecords(unittest.TestCase):
    """Test cases for deleting records from MCard databases."""

    def setUp(self):
        """Set up test environment."""
        dotenv.load_dotenv()
        self.test_db_path = Path(os.getenv('MCARD_TEST_DB', 'data/db/test/TESTONLY.db'))
        self.persistent_db_path = Path(os.getenv('MCARD_DB', 'data/db/MCardStore.db'))
        
        # Ensure test database directory exists
        self.test_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create test storage
        self.test_storage = MCardStorage(str(self.test_db_path))
        
        # Add some test records
        self.test_records = []
        for i in range(5):
            content = f"Test content {i} - {time.time()}"
            mcard = MCard(content=content)
            self.test_storage.save(mcard)
            self.test_records.append(mcard)

    def tearDown(self):
        """Clean up test environment."""
        # Remove test database
        if self.test_db_path.exists():
            os.remove(self.test_db_path)

    def test_delete_single_record(self):
        """Test deleting a single record."""
        # Get initial count
        initial_cards = self.test_storage.get_all()
        initial_count = len(initial_cards)
        
        # Delete first record
        target_hash = self.test_records[0].content_hash
        deleted = self.test_storage.delete(target_hash)
        self.assertTrue(deleted, "Delete operation should return True")
        
        # Verify record was deleted
        final_cards = self.test_storage.get_all()
        self.assertEqual(len(final_cards), initial_count - 1)
        
        # Verify record no longer exists
        deleted_card = self.test_storage.get(target_hash)
        self.assertIsNone(deleted_card)

    def test_delete_nonexistent_record(self):
        """Test deleting a record that doesn't exist."""
        # Get initial count
        initial_cards = self.test_storage.get_all()
        initial_count = len(initial_cards)
        
        # Try to delete nonexistent record
        fake_hash = "nonexistenthash123"
        deleted = self.test_storage.delete(fake_hash)
        self.assertFalse(deleted, "Delete operation should return False for nonexistent record")
        
        # Verify count hasn't changed
        final_cards = self.test_storage.get_all()
        self.assertEqual(len(final_cards), initial_count)

    def test_delete_multiple_records(self):
        """Test deleting multiple records."""
        # Get initial count
        initial_cards = self.test_storage.get_all()
        initial_count = len(initial_cards)
        
        # Delete multiple records
        deleted_count = 0
        for i in range(3):  # Delete first 3 records
            target_hash = self.test_records[i].content_hash
            if self.test_storage.delete(target_hash):
                deleted_count += 1
        
        # Verify records were deleted
        final_cards = self.test_storage.get_all()
        self.assertEqual(len(final_cards), initial_count - deleted_count)
        
        # Verify deleted records no longer exist
        for i in range(3):
            deleted_card = self.test_storage.get(self.test_records[i].content_hash)
            self.assertIsNone(deleted_card)
        
        # Verify remaining records still exist
        for i in range(3, len(self.test_records)):
            remaining_card = self.test_storage.get(self.test_records[i].content_hash)
            self.assertIsNotNone(remaining_card)

    def test_delete_and_readd_record(self):
        """Test deleting a record and then re-adding it."""
        # Get a test record
        test_record = self.test_records[0]
        test_content = test_record.content
        test_hash = test_record.content_hash
        
        # Delete the record
        deleted = self.test_storage.delete(test_hash)
        self.assertTrue(deleted)
        
        # Verify it's gone
        deleted_card = self.test_storage.get(test_hash)
        self.assertIsNone(deleted_card)
        
        # Re-add the same content
        new_mcard = MCard(content=test_content)
        saved = self.test_storage.save(new_mcard)
        self.assertTrue(saved)
        
        # Verify it was added
        readded_card = self.test_storage.get(new_mcard.content_hash)
        self.assertIsNotNone(readded_card)
        self.assertEqual(readded_card.content, test_content)
        self.assertEqual(readded_card.content_hash, test_hash)

if __name__ == '__main__':
    unittest.main()
