"""Tests for MCard domain model."""
import pytest
from mcard.domain.models.card import MCard
from datetime import datetime


def test_mcard_with_string_content():
    """Test MCard creation with string content."""
    content = "test content"
    card = MCard(content=content)
    assert card.content == content
    assert card.hash is not None
    assert isinstance(card.hash, str)
    assert "MCard(hash=" in str(card)


def test_mcard_with_bytes_content():
    """Test MCard creation with bytes content."""
    content = b"test content"
    card = MCard(content=content)
    assert card.content == content
    assert card.hash is not None


def test_mcard_g_time_format():
    """Test g_time format and timezone awareness."""
    card = MCard(content="test content")
    assert isinstance(card.g_time, str)
    assert len(card.g_time.split('.')) == 2  # Ensures microsecond precision


def test_mcard_hash_immutability():
    """Test that hash cannot be changed after creation."""
    card = MCard(content="test content")
    original_hash = card.hash
    with pytest.raises(AttributeError):
        card.hash = "new hash"
    assert card.hash == original_hash


def test_mcard_str_representation():
    """Test string representation of MCard."""
    card = MCard(content="test content")
    str_repr = str(card)
    assert "MCard" in str_repr
    assert card.hash in str_repr
    assert card.g_time in str_repr
