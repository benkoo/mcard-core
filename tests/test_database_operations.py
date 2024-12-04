import sqlite3
import unittest
from pathlib import Path
from mcard.config_constants import DEFAULT_DB_PATH
from mcard.application.card_provisioning_app import CardProvisioningApp
from unittest.mock import AsyncMock
from mcard.domain.models.card import MCard

class TestDatabaseOperations(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Ensure the database file exists
        self.db_path = Path(DEFAULT_DB_PATH)
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the table if it doesn't exist
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)')

        # Mock the CardStore
        self.mock_store = AsyncMock()
        self.app = CardProvisioningApp(store=self.mock_store)

    async def asyncTearDown(self):
        # Remove the test_table after each test
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DROP TABLE IF EXISTS test_table')

    async def test_create_and_retrieve_card(self):
        # Mock the save and get methods
        self.mock_store.save = AsyncMock()
        self.mock_store.get = AsyncMock(return_value=MCard(content=b'Test Content'))

        # Create a card
        card = await self.app.create_card('Test Content')
        self.mock_store.save.assert_awaited_with(card)

        # Retrieve the card
        retrieved_card = await self.app.retrieve_card(card.hash)
        self.mock_store.get.assert_awaited_with(card.hash)
        self.assertEqual(retrieved_card.content, b'Test Content')

    async def test_database_file_exists(self):
        # Check if the database file exists
        self.assertTrue(self.db_path.exists(), f"Database file {self.db_path} does not exist.")

if __name__ == '__main__':
    unittest.main()
