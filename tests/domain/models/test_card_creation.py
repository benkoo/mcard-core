"""Tests for MCard creation with various content types."""
import pytest
from mcard.domain.models.card import MCard


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


def test_mcard_none_content():
    """Test MCard with None content raises exception."""
    with pytest.raises(TypeError):
        MCard(content=None)
