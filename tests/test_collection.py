"""Tests for the MCardCollection class."""
import os
import pytest
from datetime import datetime, timedelta, timezone
from mcard.core import MCard
from mcard.storage import MCardStorage
from mcard.collection import MCardCollection
import time

@pytest.fixture
def storage():
    """Create a temporary storage for testing."""
    db_path = "test_collection.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    storage = MCardStorage(db_path)
    yield storage
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def collection(storage):
    """Create a collection instance for testing."""
    return MCardCollection(storage)

def test_collection_initialization(collection):
    """Test that collection initializes and loads cards."""
    cards = collection.get_all_cards()
    assert isinstance(cards, list)
    # Verify cards are sorted by time_claimed
    if len(cards) > 1:
        for i in range(len(cards)-1):
            assert cards[i].time_claimed <= cards[i+1].time_claimed

def test_add_and_get_card(collection):
    """Test adding a new card and retrieving it."""
    # Create a new card with unique content
    unique_content = f"Test card content {time.time()}"
    card = MCard(content=unique_content)
    
    # Add the card
    success = collection.add_card(card)
    assert success is True
    
    # Verify the card was added
    cards = collection.get_all_cards()
    assert any(c.content == unique_content for c in cards)
    
    # Verify we can get it by hash
    retrieved = collection.get_card_by_hash(card.content_hash)
    assert retrieved is not None
    assert retrieved.content == unique_content

def test_temporal_order_comparison(collection):
    """Test comparing cards by temporal order."""
    # Create two cards with different timestamps
    card1 = MCard(content="First card")
    time.sleep(0.1)  # Ensure different timestamps
    card2 = MCard(content="Second card")
    
    assert collection.compare_cards_temporal_order(card1, card2) == -1
    assert collection.compare_cards_temporal_order(card2, card1) == 1
    assert collection.compare_cards_temporal_order(card1, card1) == 0

def test_get_cards_in_timerange(collection):
    """Test getting cards within a time range."""
    # Create cards with different timestamps using timezone-aware datetimes
    now = datetime.now(timezone.utc)
    card1 = MCard(content="Card 1", time_claimed=now - timedelta(hours=1))
    card2 = MCard(content="Card 2", time_claimed=now)
    
    collection.add_card(card1)
    collection.add_card(card2)
    
    # Test range that should include both cards
    cards = collection.get_cards_in_timerange(
        now - timedelta(hours=2),
        now + timedelta(hours=1)
    )
    assert len(cards) >= 2
    
    # Verify the cards are within the time range
    for card in cards:
        assert now - timedelta(hours=2) <= card.time_claimed <= now + timedelta(hours=1)

def test_remove_card(collection):
    """Test removing a card."""
    # Add a card
    card = MCard(content="Card to remove")
    collection.add_card(card)
    
    # Remove it
    success = collection.remove_card(card.content_hash)
    assert success is True
    
    # Verify it's gone
    retrieved = collection.get_card_by_hash(card.content_hash)
    assert retrieved is None

def test_refresh(collection):
    """Test refreshing the collection."""
    # Get initial state
    initial_cards = collection.get_all_cards()
    initial_count = len(initial_cards)
    
    # Add a new card directly to storage with unique content
    unique_content = f"Refresh test card {time.time()}"
    card = MCard(content=unique_content)
    collection.storage.save(card)
    collection.storage.conn.commit()  # Ensure the transaction is committed
    
    # Refresh and verify new card is loaded
    collection.refresh()
    refreshed_cards = collection.get_all_cards()
    assert len(refreshed_cards) > initial_count
    assert any(c.content == unique_content for c in refreshed_cards)
