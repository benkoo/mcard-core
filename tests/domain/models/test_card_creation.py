"""Tests for MCard creation with various content types."""
import pytest
from typing import Optional, List, Union
from datetime import datetime, timezone
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore
from mcard.domain.models.hashing_protocol import HashingService
from mcard.domain.services.hashing import get_hashing_service


def test_mcard_with_string_content():
    """Test MCard creation with string content."""
    content = "test content"
    card = MCard(content=content)
    assert card.content == content.encode('utf-8')  # Content should be stored as bytes
    assert card.hash is not None
    assert isinstance(card.hash, str)
    assert "MCard(hash=" in str(card)


def test_mcard_with_bytes_content():
    """Test MCard creation with bytes content."""
    content = b"test content"
    card = MCard(content=content)
    assert card.content == content
    assert card.hash is not None
    assert isinstance(card.hash, str)


def test_mcard_none_content():
    """Test MCard with None content raises exception."""
    with pytest.raises(TypeError):
        MCard(content=None)


def test_mcard_with_empty_content():
    """Test MCard creation with empty content."""
    content = ""
    card = MCard(content=content)
    assert card.content == b""
    assert card.hash is not None
    assert isinstance(card.hash, str)


def test_mcard_hash_uniqueness():
    """Test that different content produces different hashes."""
    card1 = MCard(content="content1")
    card2 = MCard(content="content2")
    assert card1.hash != card2.hash


def test_mcard_hash_consistency():
    """Test that same content produces same hash."""
    content = "test content"
    card1 = MCard(content=content)
    card2 = MCard(content=content)
    assert card1.hash == card2.hash


def test_mcard_with_special_characters():
    """Test MCard creation with special characters."""
    content = "Special 😀 characters 🌟 test"
    card = MCard(content=content)
    assert card.content == content.encode('utf-8')
    assert card.hash is not None


def test_mcard_with_binary_data():
    """Test MCard creation with binary data."""
    content = bytes([0x00, 0x01, 0x02, 0x03])
    card = MCard(content=content)
    assert card.content == content
    assert card.hash is not None
