"""Tests for MCard domain model."""
import pytest
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.services.hashing import get_hashing_service
from pydantic import ValidationError

def test_mcard_with_string_content():
    """Test MCard creation with string content."""
    content = "test content"
    card = MCard(content=content)
    assert card.content == content
    assert card.hash is not None
    assert isinstance(card.hash, str)
    assert card.g_time.tzinfo is not None  # Ensure timezone aware

def test_mcard_with_bytes_content():
    """Test MCard creation with bytes content."""
    content = b"test content"
    card = MCard(content=content)
    assert card.content == content
    assert card.hash is not None
    # Hash should be same for equivalent string and bytes
    str_card = MCard(content="test content")
    assert card.hash == str_card.hash

def test_mcard_with_object_content():
    """Test MCard creation with object content."""
    content = {"key": "value"}
    card = MCard(content=content)
    assert card.content == content
    assert card.hash is not None

def test_mcard_with_preexisting_hash():
    """Test MCard creation with pre-existing hash."""
    content = "test content"
    existing_hash = get_hashing_service().hash_content(content.encode())
    card = MCard(content=content, hash=existing_hash)
    assert card.hash == existing_hash

def test_mcard_hash_immutability():
    """Test that hash cannot be changed after creation."""
    card = MCard(content="test content")
    original_hash = card.hash
    with pytest.raises(ValidationError):
        card.hash = "new hash"
    assert card.hash == original_hash

def test_mcard_g_time_timezone_awareness():
    """Test g_time timezone awareness."""
    # Test with naive datetime
    naive_time = datetime.now()
    card = MCard(content="test", g_time=naive_time)
    assert card.g_time.tzinfo is not None

    # Test with aware datetime
    aware_time = datetime.now(timezone.utc)
    card = MCard(content="test", g_time=aware_time)
    assert card.g_time.tzinfo is not None
    assert card.g_time == aware_time

def test_mcard_extra_fields():
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError):
        MCard(content="test", extra_field="value")

def test_mcard_str_representation():
    """Test string representation of MCard."""
    card = MCard(content="test")
    str_repr = str(card)
    assert "MCard" in str_repr
    assert "hash=" in str_repr
    assert "time=" in str_repr
    assert card.hash in str_repr

def test_mcard_content_update():
    """Test updating MCard content."""
    # Since hash is frozen, we need to create a new MCard when content changes
    card = MCard(content="initial")
    initial_hash = card.hash
    updated_card = MCard(content="updated")
    assert updated_card.content == "updated"
    assert updated_card.hash != initial_hash  # Hash should be different for different content

def test_mcard_none_content():
    """Test MCard with None content."""
    card = MCard(content=None)
    assert card.content is None
    assert card.hash is not None  # Should still generate hash for None
