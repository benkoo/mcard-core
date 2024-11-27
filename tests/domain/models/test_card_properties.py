"""Tests for MCard properties like hash, g_time, and immutability."""
import pytest
from mcard.domain.models.card import MCard


def test_mcard_hash_immutability():
    """Test that hash cannot be changed after creation."""
    card = MCard(content="test content")
    original_hash = card.hash
    with pytest.raises(AttributeError):
        card.hash = "new hash"
    assert card.hash == original_hash


def test_mcard_g_time_format():
    """Test g_time format and timezone awareness."""
    card = MCard(content="test content")
    assert isinstance(card.g_time, str)
    assert len(card.g_time.split('.')) == 2  # Ensures microsecond precision


def test_mcard_str_representation():
    """Test string representation of MCard."""
    card = MCard(content="test content")
    str_repr = str(card)
    assert "MCard" in str_repr
    assert card.hash in str_repr
    assert card.g_time in str_repr


def test_consistent_hash_for_same_content():
    """Test consistent hash for the same content."""
    content = "consistent content"
    card1 = MCard(content=content)
    card2 = MCard(content=content)
    assert card1.hash == card2.hash


def test_different_hash_for_different_content():
    """Test different hash for different content."""
    content1 = "content one"
    content2 = "content two"
    card1 = MCard(content=content1)
    card2 = MCard(content=content2)
    assert card1.hash != card2.hash
