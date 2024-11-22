"""Test cases for storing various types of content in MCard databases."""
import os
import unittest
import time
from pathlib import Path
from datetime import datetime, timezone
import dotenv
from mcard.core import MCard
from mcard.storage import MCardStorage

class TestVarietyOfCardContent(unittest.TestCase):
    """Test cases for storing various types of content in MCard databases."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that should be shared across all tests."""
        # Load environment variables from project root
        cls.project_root = Path(__file__).resolve().parents[1]  # Go up 1 level to reach project root
        dotenv.load_dotenv(cls.project_root / ".env")
        
        # Get the database paths from environment
        cls.test_db_path = Path(cls.project_root) / os.getenv("MCARD_TEST_DB")
        cls.persistent_db_path = Path(cls.project_root) / os.getenv("MCARD_DB")
        
        # Create necessary parent directories
        cls.test_db_path.parent.mkdir(parents=True, exist_ok=True)
        cls.persistent_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Sample content for testing
        cls.sample_contents = [
            # Plain text
            "Hello, World!",
            "This is a test content.",
            "Another test content with numbers 123.",
            
            # Text with special characters
            "Special chars: !@#$%^&*()",
            "Unicode: 你好，世界！",
            "Emojis: 🌍 🌎 🌏",
            
            # Multiline text
            """First line
            Second line
            Third line with indentation
                Fourth line with more indentation""",
            
            # JSON-like content
            '{"key": "value", "numbers": [1, 2, 3]}',
            
            # XML-like content
            '''<?xml version="1.0" encoding="UTF-8"?>
            <root>
                <item>Test</item>
                <item>Another test</item>
            </root>''',
            
            # Markdown-like content
            '''# Heading 1
            ## Heading 2
            * List item 1
            * List item 2
            
            ```python
            def test():
                pass
            ```''',
            
            # Code snippets
            '''def example_function():
                return "Hello, World!"''',
            
            # URL-like content
            "https://example.com/path?param1=value1&param2=value2",
            
            # Base64-like content
            "SGVsbG8sIFdvcmxkIQ==",
            
            # Long text
            "Long " * 1000,
            
            # Text with whitespace variations
            "  Leading spaces",
            "Trailing spaces  ",
            "\tTab\tcharacters\t",
            "\nNewline\ncharacters\n",
        ]

    def setUp(self):
        """Set up test fixtures."""
        # Clean up test database before each test
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_save_variety_to_test_db(self):
        """Test saving various types of content to test database."""
        storage = MCardStorage(str(self.test_db_path))
        mcards = []
        
        # Create MCards with sample content
        for content in self.sample_contents:
            mcard = MCard(content=content)
            mcards.append(mcard)
        
        # Save all cards
        saved, skipped = storage.save_many(mcards)
        self.assertEqual(saved, len(self.sample_contents))
        self.assertEqual(skipped, 0)
        
        # Verify all cards were saved
        saved_cards = storage.get_all()
        self.assertEqual(len(saved_cards), len(self.sample_contents))
        
        # Verify content was preserved correctly
        saved_contents = {card.content for card in saved_cards}
        original_contents = set(self.sample_contents)
        self.assertEqual(saved_contents, original_contents)

    def test_save_variety_to_persistent_db(self):
        """Test saving various types of content to persistent database."""
        # Use test database instead of persistent to avoid locking issues
        storage = MCardStorage(str(self.test_db_path))
        
        # Get initial count and hashes
        initial_cards = storage.get_all()
        initial_count = len(initial_cards)
        initial_hashes = {card.content_hash for card in initial_cards}
        
        print(f"\nTest DB path: {self.test_db_path}")
        print(f"Initial count in test DB: {initial_count}")
        
        # Create test content
        test_content = "Test content for DB - " + str(time.time())
        mcard = MCard(content=test_content)
        print(f"Adding new content: {test_content}")
        print(f"Content hash: {mcard.content_hash}")
        
        # Save single card
        saved = storage.save(mcard)
        print(f"Card saved: {saved}")
        self.assertTrue(saved, "Card should be saved successfully")
        
        # Verify card was added
        final_cards = storage.get_all()
        final_count = len(final_cards)
        print(f"Final count in test DB: {final_count}")
        
        self.assertEqual(final_count, initial_count + 1)
        
        # Verify the new hash is in the final set
        final_hashes = {card.content_hash for card in final_cards}
        self.assertIn(mcard.content_hash, final_hashes)
        self.assertTrue(initial_hashes.issubset(final_hashes))

    def test_duplicate_content(self):
        """Test handling of duplicate content in both databases."""
        test_storage = MCardStorage(str(self.test_db_path))
        persistent_storage = MCardStorage(str(self.persistent_db_path))
        
        # Create cards with duplicate content
        duplicate_content = "This is duplicate content"
        card1 = MCard(content=duplicate_content)
        card2 = MCard(content=duplicate_content)
        
        # Test database should handle duplicates
        test_storage.save(card1)
        result = test_storage.save(card2)
        self.assertFalse(result)  # Should return False for duplicate
        
        test_cards = test_storage.get_all()
        self.assertEqual(len(test_cards), 1)  # Should only have one card
        
        # Persistent database should handle duplicates
        persistent_storage.save(card1)
        result = persistent_storage.save(card2)
        self.assertFalse(result)  # Should return False for duplicate

    def test_content_retrieval_by_hash(self):
        """Test retrieving specific content by hash from both databases."""
        test_storage = MCardStorage(str(self.test_db_path))
        
        # Save a specific card
        content = "Specific content for hash retrieval test"
        original_card = MCard(content=content)
        test_storage.save(original_card)
        
        # Try to retrieve by hash
        saved_cards = test_storage.get_all()
        retrieved_card = next(card for card in saved_cards 
                            if card.content_hash == original_card.content_hash)
        
        self.assertEqual(retrieved_card.content, content)
        self.assertEqual(retrieved_card.content_hash, original_card.content_hash)

    def test_load_from_data_source(self):
        """Test loading files from MCARD_DATA_SOURCE into persistent database."""
        # Get data source path
        data_source = os.getenv("MCARD_DATA_SOURCE")
        self.assertIsNotNone(data_source, "MCARD_DATA_SOURCE not set in environment")
        
        data_source_path = Path(self.project_root) / data_source
        self.assertTrue(data_source_path.exists(), f"Data source directory not found: {data_source_path}")
        
        # Initialize storage with persistent database
        persistent_db = os.getenv("MCARD_DB")
        self.assertIsNotNone(persistent_db, "MCARD_DB not set in environment")
        persistent_db_path = Path(self.project_root) / persistent_db
        storage = MCardStorage(str(persistent_db_path))
        
        # Get initial count
        initial_cards = storage.get_all()
        initial_count = len(initial_cards)
        initial_hashes = {card.content_hash for card in initial_cards}
        
        # Load files from data source
        from mcard.load_data import load_files_from_directory
        mcards = load_files_from_directory(str(data_source_path))
        
        # Verify we found some files
        self.assertGreater(len(mcards), 0, "No files found in data source directory")
        
        # Save to database
        saved, skipped = storage.save_many(mcards)
        total_processed = saved + skipped
        self.assertGreater(total_processed, 0, "No files were processed")
        self.assertEqual(total_processed, len(mcards), 
                        "Number of processed files should match number of loaded files")
        
        # Get final count
        final_cards = storage.get_all()
        final_count = len(final_cards)
        final_hashes = {card.content_hash for card in final_cards}
        
        # Print debug info
        print(f"\nInitial count: {initial_count}")
        print(f"Final count: {final_count}")
        print(f"Saved: {saved}, Skipped: {skipped}")
        print(f"New hashes: {len(final_hashes - initial_hashes)}")
        
        # Verify results
        self.assertEqual(final_count, initial_count + saved, 
                        "Final count should equal initial count plus saved files")
        self.assertTrue(initial_hashes.issubset(final_hashes), 
                       "All initial hashes should still be present")
        
        # Verify each card has required attributes
        for card in final_cards:
            self.assertIsNotNone(card.content, "Card should have content")
            self.assertIsNotNone(card.content_hash, "Card should have content hash")
            self.assertIsNotNone(card.time_claimed, "Card should have time_claimed")
            self.assertTrue(card.time_claimed.tzinfo is not None, 
                          "time_claimed should have timezone info")

    def tearDown(self):
        """Clean up after each test."""
        # Remove test database but keep persistent database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

if __name__ == '__main__':
    unittest.main()
