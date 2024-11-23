"""Performance tests for MCard operations with large datasets."""
import os
import unittest
import time
import random
import json
import string
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta
from mcard import config
from mcard.core import MCard
from mcard.storage import MCardStorage

# Default number of cards for performance testing if not specified in environment
DEFAULT_TEST_CARDS = 100

class TestMCardPerformance(unittest.TestCase):
    """Test cases for MCard performance with large datasets."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that should be shared across all tests."""
        # Load environment variables using mcard.config
        config.load_config()
        
        # Get the database paths using config functions
        cls.test_db_path = Path(config.get_db_path(test=True))
        cls.persistent_db_path = Path(config.get_db_path(test=False))
        
        # Get number of test cards from environment, default to DEFAULT_TEST_CARDS
        try:
            cls.num_test_cards = int(os.getenv("MCARD_PERF_TEST_CARDS", str(DEFAULT_TEST_CARDS)))
        except (TypeError, ValueError):
            print(f"Warning: Invalid MCARD_PERF_TEST_CARDS value, using default ({DEFAULT_TEST_CARDS})")
            cls.num_test_cards = DEFAULT_TEST_CARDS
        
        # Create necessary parent directories
        cls.test_db_path.parent.mkdir(parents=True, exist_ok=True)
        cls.persistent_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize random seed for reproducibility
        random.seed(42)
        np.random.seed(42)

    def generate_random_content(self):
        """Generate random content of different types."""
        content_types = [
            self._generate_text,
            self._generate_number,
            self._generate_json,
            self._generate_binary,
            self._generate_multiline_text,
            self._generate_structured_data
        ]
        return random.choice(content_types)()

    def _generate_text(self, length=100):
        """Generate random text content."""
        return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation + ' ', k=length))

    def _generate_number(self):
        """Generate random numeric content."""
        return str(random.uniform(-1000000, 1000000))

    def _generate_json(self):
        """Generate random JSON content."""
        data = {
            'id': random.randint(1, 1000000),
            'name': ''.join(random.choices(string.ascii_letters, k=10)),
            'values': [random.randint(1, 100) for _ in range(5)],
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'type': random.choice(['type1', 'type2', 'type3']),
                'tags': [f'tag{i}' for i in random.sample(range(1, 10), 3)]
            }
        }
        return json.dumps(data)

    def _generate_binary(self):
        """Generate random binary content."""
        return np.random.bytes(random.randint(100, 1000))

    def _generate_multiline_text(self):
        """Generate random multiline text content."""
        lines = []
        for _ in range(random.randint(3, 10)):
            lines.append(self._generate_text(length=random.randint(20, 80)))
        return '\n'.join(lines)

    def _generate_structured_data(self):
        """Generate random structured data content."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item id="{random.randint(1, 1000)}">
        <name>{self._generate_text(20)}</name>
        <value>{random.uniform(0, 100):.2f}</value>
        <timestamp>{datetime.now().isoformat()}</timestamp>
    </item>
</root>'''

    def _run_performance_test(self, num_cards: int):
        """Run a performance test with the specified number of cards."""
        # Create a new storage instance
        storage = MCardStorage(self.test_db_path)
        
        # Clean existing data
        existing_cards = storage.get_all()
        for card in existing_cards:
            storage.delete(card.content_hash)
        
        # Generate and store cards
        start_time = time.time()
        cards = []
        
        print(f"\nGenerating and storing {num_cards:,} random MCards...")
        for i in range(num_cards):
            content = self.generate_random_content()
            # Create cards with timestamps spread over the last 30 days
            time_claimed = datetime.now(timezone.utc) - timedelta(
                days=random.uniform(0, 30),
                hours=random.uniform(0, 24),
                minutes=random.uniform(0, 60)
            )
            
            card = MCard(content=content, time_claimed=time_claimed)
            cards.append(card)
            
            if (i + 1) % (num_cards // 10) == 0:  # Show progress every 10%
                print(f"Generated {i + 1:,} cards ({((i + 1) / num_cards * 100):.1f}%)...")
        
        # Measure storage time
        storage_start = time.time()
        batch_size = 100  # Store in batches to improve performance
        for i in range(0, len(cards), batch_size):
            batch = cards[i:i + batch_size]
            for card in batch:
                storage.save(card)
            if (i + batch_size) % (num_cards // 10) == 0:  # Show progress every 10%
                print(f"Stored {i + batch_size:,} cards ({((i + batch_size) / num_cards * 100):.1f}%)...")
        storage_time = time.time() - storage_start
        
        # Measure retrieval time
        retrieval_start = time.time()
        retrieved_cards = storage.get_all()
        retrieval_time = time.time() - retrieval_start
        
        total_time = time.time() - start_time
        
        # Print performance metrics
        print(f"\nPerformance Metrics for {num_cards:,} cards:")
        print(f"Total cards stored: {num_cards:,}")
        print(f"Storage time: {storage_time:.2f} seconds")
        print(f"Average storage time per card: {storage_time/num_cards:.4f} seconds")
        print(f"Retrieval time for all cards: {retrieval_time:.2f} seconds")
        print(f"Average retrieval time per card: {retrieval_time/num_cards:.4f} seconds")
        print(f"Total operation time: {total_time:.2f} seconds")
        print(f"Database size: {Path(self.test_db_path).stat().st_size / (1024*1024):.2f} MB")
        
        # Verify data integrity
        self.assertEqual(len(retrieved_cards), num_cards)
        
        # Clean up - delete each card individually since there's no bulk delete
        print("\nCleaning up...")
        for i, card in enumerate(retrieved_cards):
            storage.delete(card.content_hash)
            if (i + 1) % (num_cards // 10) == 0:  # Show progress every 10%
                print(f"Deleted {i + 1:,} cards ({((i + 1) / num_cards * 100):.1f}%)...")

    def test_load_random_cards(self):
        """Test loading and retrieving random MCards.
        
        The number of cards is configured through MCARD_PERF_TEST_CARDS
        environment variable (defaults to DEFAULT_TEST_CARDS if not set
        or if the value is invalid).
        """
        self._run_performance_test(self.num_test_cards)

if __name__ == '__main__':
    unittest.main()
