"""Tests for custom hash function."""
import pytest
from mcard.domain.models.protocols import HashingService
from mcard.domain.services.hashing import HashingSettings, HashingError
from mcard.domain.dependency.custom_hash_md5 import custom_md5_hash, create_md5_hasher

def test_custom_md5_hash_direct():
    """Test custom_md5_hash function directly."""
    content = b"Hello, World!"
    hash_value = custom_md5_hash(content)
    assert len(hash_value) == 32  # MD5 produces 32-character hex strings
    assert hash_value == "65a8e27d8879283831b664bd8b7f0ad4"  # Known MD5 hash for "Hello, World!"

def test_custom_md5_hash_with_service():
    """Test custom_md5_hash through HashingService."""
    settings = HashingSettings(
        algorithm="custom",
        custom_module="mcard.domain.dependency.custom_hash_md5",
        custom_function="create_md5_hasher",
        custom_hash_length=32  # MD5 produces 32-character hex strings
    )
    
    service = HashingService(settings)
    content = b"Hello, World!"
    hash_value = service.hash_content(content)
    
    assert hash_value == "65a8e27d8879283831b664bd8b7f0ad4"  # Known MD5 hash for "Hello, World!"

def test_custom_md5_hash_empty_content():
    """Test custom_md5_hash with empty content."""
    with pytest.raises(ValueError):
        custom_md5_hash(b"")

def test_custom_md5_hash_invalid_type():
    """Test custom_md5_hash with invalid input type."""
    with pytest.raises(TypeError):
        custom_md5_hash("not bytes")  # Should be bytes, not str

def test_custom_md5_hash_service_empty_content():
    """Test HashingService with custom MD5 hash on empty content."""
    settings = HashingSettings(
        algorithm="custom",
        custom_module="mcard.domain.dependency.custom_hash_md5",
        custom_function="create_md5_hasher",
        custom_hash_length=32
    )
    
    service = HashingService(settings)
    with pytest.raises(HashingError):
        service.hash_content(b"")
