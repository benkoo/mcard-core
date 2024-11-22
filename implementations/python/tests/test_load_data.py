"""Test cases for MCard data loading functionality."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
import dotenv
from mcard.core import MCard
from mcard.storage import MCardStorage
from mcard.load_data import load_files_from_directory, main

class TestMCardDataLoading(unittest.TestCase):
    """Test cases for MCard data loading functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that should be shared across all tests."""
        # Load environment variables from project root
        cls.project_root = Path(__file__).resolve().parents[3]  # Go up 3 levels to reach project root
        dotenv.load_dotenv(cls.project_root / ".env")
        
        # Get the database paths from environment
        cls.test_db_path = Path(cls.project_root) / os.getenv("MCARD_TEST_DB")
        cls.persistent_db_path = Path(cls.project_root) / os.getenv("MCARD_DB")
        
        # Create necessary parent directories
        cls.test_db_path.parent.mkdir(parents=True, exist_ok=True)
        cls.persistent_db_path.parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "data")
        self.cards_dir = os.path.join(self.data_dir, "cards")
        os.makedirs(self.cards_dir)
        
        # Store original working directory and environment
        self.original_cwd = os.getcwd()
        self.original_env = os.environ.copy()
        
        # Set environment variable for test data source
        os.environ["MCARD_DATA_SOURCE"] = self.cards_dir
        
        # Create test files
        self.create_test_files()
        
        # Change to temp directory
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original working directory and environment
        os.chdir(self.original_cwd)
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Clean up test database but keep persistent database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def create_test_files(self):
        """Create test files with different content types."""
        # Text file
        text_path = os.path.join(self.cards_dir, "test.txt")
        with open(text_path, "w") as f:
            f.write("Hello, World!")
        
        # Binary file
        binary_path = os.path.join(self.cards_dir, "test.bin")
        with open(binary_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03")
        
        # Nested directory with files
        nested_dir = os.path.join(self.cards_dir, "nested")
        os.makedirs(nested_dir)
        with open(os.path.join(nested_dir, "nested.txt"), "w") as f:
            f.write("Nested file content")

    def test_load_files_from_directory(self):
        """Test loading files from a directory."""
        mcards = load_files_from_directory(self.cards_dir)
        
        # Should find 3 files (test.txt, test.bin, nested/nested.txt)
        self.assertEqual(len(mcards), 3)
        
        # Verify each MCard has required attributes
        for mcard in mcards:
            self.assertIsInstance(mcard, MCard)
            self.assertIsNotNone(mcard.content)
            self.assertIsNotNone(mcard.content_hash)
            self.assertIsInstance(mcard.time_claimed, datetime)
            self.assertIsNotNone(mcard.time_claimed.tzinfo)

    def test_load_and_save_to_test_db(self):
        """Test loading files and saving to test database."""
        # Initialize storage with test database
        storage = MCardStorage(str(self.test_db_path))
        
        # Load files
        mcards = load_files_from_directory(self.cards_dir)
        
        # Save to database
        saved, skipped = storage.save_many(mcards)
        self.assertEqual(saved, 3)  # All 3 files should be saved
        self.assertEqual(skipped, 0)  # Nothing should be skipped
        
        # Try saving again
        saved, skipped = storage.save_many(mcards)
        self.assertEqual(saved, 0)    # Nothing new to save
        self.assertEqual(skipped, 3)  # All should be skipped

    def test_load_and_save_to_persistent_db(self):
        """Test loading files and saving to persistent database."""
        # Initialize storage with persistent database
        storage = MCardStorage(str(self.persistent_db_path))
        
        # Load files
        mcards = load_files_from_directory(self.cards_dir)
        
        # Get initial count
        initial_count = len(storage.get_all())
        
        # Save to database
        saved, skipped = storage.save_many(mcards)
        
        # Verify new records were added
        final_count = len(storage.get_all())
        self.assertEqual(final_count, initial_count + saved)

    def test_main_function(self):
        """Test the main function using environment variables."""
        # Set test database for main function
        os.environ["MCARD_DB"] = str(self.test_db_path)
        
        # Run main function
        main()
        
        # Verify database was created
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Check that files were loaded
        storage = MCardStorage(str(self.test_db_path))
        all_cards = storage.get_all()
        self.assertEqual(len(all_cards), 3)  # Should have loaded all 3 test files

    def test_main_function_with_duplicates(self):
        """Test the main function handles duplicates correctly."""
        # Set test database for main function
        os.environ["MCARD_DB"] = str(self.test_db_path)
        
        # Run main function first time
        main()
        
        # Create a new file
        new_file_path = os.path.join(self.cards_dir, "new.txt")
        with open(new_file_path, "w") as f:
            f.write("New file content")
        
        # Run main function again
        main()
        
        # Check database
        storage = MCardStorage(str(self.test_db_path))
        all_cards = storage.get_all()
        self.assertEqual(len(all_cards), 4)  # Should have 3 original files + 1 new file

    def test_directories_not_saved(self):
        """Test that directories are not saved as records."""
        # Create some nested directories
        nested_dirs = [
            os.path.join(self.cards_dir, "dir1"),
            os.path.join(self.cards_dir, "dir1", "subdir1"),
            os.path.join(self.cards_dir, "dir2"),
        ]
        for d in nested_dirs:
            os.makedirs(d)
        
        # Create a file in one of the directories
        file_path = os.path.join(nested_dirs[0], "test.txt")
        with open(file_path, "w") as f:
            f.write("Test content")
        
        # Initialize storage with test database
        storage = MCardStorage(str(self.test_db_path))
        
        # Load files
        mcards = load_files_from_directory(self.cards_dir)
        
        # Count how many files we expect (3 from create_test_files + 1 new file)
        expected_files = 4
        
        # Verify we only got files, not directories
        self.assertEqual(len(mcards), expected_files)
        
        # Verify each MCard is from a file, not a directory
        for mcard in mcards:
            # Content should not be empty (directories would have empty content)
            self.assertTrue(mcard.content)
            self.assertTrue(mcard.content_hash)
        
        # Save to database
        saved, skipped = storage.save_many(mcards)
        self.assertEqual(saved, expected_files)
        self.assertEqual(skipped, 0)
        
        # Verify database only contains the expected number of records
        all_cards = storage.get_all()
        self.assertEqual(len(all_cards), expected_files)

    def test_error_handling(self):
        """Test error handling for invalid paths and files."""
        # Test with non-existent directory
        with self.assertRaises(FileNotFoundError):
            load_files_from_directory("/nonexistent/path")
        
        # Test with file that becomes inaccessible
        test_file = os.path.join(self.cards_dir, "temp.txt")
        with open(test_file, "w") as f:
            f.write("Temporary content")
        
        # Make file unreadable (if running as non-root)
        try:
            os.chmod(test_file, 0)
            mcards = load_files_from_directory(self.cards_dir)
            # Should still load other files even if one fails
            self.assertEqual(len(mcards), 3)
        finally:
            # Restore permissions so file can be deleted
            os.chmod(test_file, 0o666)

if __name__ == '__main__':
    unittest.main()
