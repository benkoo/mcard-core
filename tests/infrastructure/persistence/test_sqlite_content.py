"""Tests for content handling in SQLite card repository."""
import pytest
import os
import tempfile
from mcard.infrastructure.persistence.sqlite import SQLiteCardRepository, SchemaInitializer
from mcard.domain.models.card import MCard
import logging

# Ensure the log file is cleared before each test run
if os.path.exists('test.log'):
    os.remove('test.log')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('test.log')  # Output to file
    ]
)

@pytest.fixture
def db_path():
    """Fixture for temporary database path."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup after tests
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def repository(db_path):
    """Fixture for SQLite repository."""
    repo = SQLiteCardRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    return repo

def test_binary_content(repository):
    repo = repository
    binary_content = bytes([0, 1, 2, 3, 4])
    card = MCard(content=binary_content)
    repo.save(card)
    retrieved_card = repo.get(card.hash)
    assert retrieved_card.content == binary_content

def test_large_content_handling(db_path):
    repo = SQLiteCardRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    logging.debug("Testing large content handling")
    large_content = "x" * (10 * 1024 * 1024)  # 10MB
    card = MCard(content=large_content)
    repo.save(card)
    retrieved_card = repo.get(card.hash)
    assert retrieved_card.content == large_content

def test_binary_and_text_content(db_path):
    repo = SQLiteCardRepository(db_path)
    SchemaInitializer.initialize_schema(repo.connection)
    logging.debug("Testing binary and text content handling")
    binary_content = bytes([0, 1, 2, 3, 4])
    text_content = "Hello, World!"
    card1 = MCard(content=binary_content)
    card2 = MCard(content=text_content)
    repo.save(card1)
    repo.save(card2)
    retrieved_card1 = repo.get(card1.hash)
    retrieved_card2 = repo.get(card2.hash)
    assert retrieved_card1.content == binary_content
    assert retrieved_card2.content == text_content
