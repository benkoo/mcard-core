"""
Tests for hashing service implementation.
"""
import pytest
from mcard.domain.services.hashing import (
    DefaultHashingService,
    get_hashing_service,
    set_hashing_service,
)
from mcard.domain.models.config import HashFunction, HashingSettings
from mcard.domain.models.exceptions import HashingError

@pytest.fixture
def default_service():
    """Create a default hashing service with SHA256."""
    settings = HashingSettings(algorithm=HashFunction.SHA256)
    return DefaultHashingService(settings)

def test_hash_content_sha256():
    """Test hashing with SHA256."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA256))
    content = b"test content"
    hash_str = service.hash_content(content)
    assert len(hash_str) == 64  # SHA256 produces 64 character hex string
    assert hash_str == "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"

def test_hash_content_sha512():
    """Test hashing with SHA512."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA512))
    content = b"test content"
    hash_str = service.hash_content(content)
    assert len(hash_str) == 128  # SHA512 produces 128 character hex string

def test_hash_content_sha1():
    """Test hashing with SHA1."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA1))
    content = b"test content"
    hash_str = service.hash_content(content)
    assert len(hash_str) == 40  # SHA1 produces 40 character hex string

def test_hash_content_md5():
    """Test hashing with MD5."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.MD5))
    content = b"test content"
    hash_str = service.hash_content(content)
    assert len(hash_str) == 32  # MD5 produces 32 character hex string

def test_validate_hash_valid():
    """Test hash validation with valid hash."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA256))
    valid_hash = "a" * 64  # Valid SHA256 hash length
    assert service.validate_hash(valid_hash) is True

def test_validate_hash_invalid_length():
    """Test hash validation with invalid length."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA256))
    invalid_hash = "a" * 63  # Invalid SHA256 hash length
    assert service.validate_hash(invalid_hash) is False

def test_validate_hash_invalid_chars():
    """Test hash validation with invalid characters."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA256))
    invalid_hash = "g" * 64  # Contains invalid hex character
    assert service.validate_hash(invalid_hash) is False

def test_custom_hash_function_missing_settings():
    """Test custom hash function with missing settings."""
    settings = HashingSettings(algorithm=HashFunction.CUSTOM)
    with pytest.raises(HashingError, match="Custom hash function requires"):
        DefaultHashingService(settings)

def test_custom_hash_function_invalid_module():
    """Test custom hash function with invalid module."""
    settings = HashingSettings(
        algorithm=HashFunction.CUSTOM,
        custom_module="nonexistent_module",
        custom_function="hash_func",
        custom_hash_length=32
    )
    with pytest.raises(HashingError, match="Failed to load custom hash function"):
        DefaultHashingService(settings)

def test_global_service_instance():
    """Test global service instance management."""
    # Clear any existing service
    set_hashing_service(None)
    
    # Get default service
    service1 = get_hashing_service()
    assert isinstance(service1, DefaultHashingService)
    
    # Set custom service
    custom_service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA512))
    set_hashing_service(custom_service)
    
    # Get should return the custom service
    service2 = get_hashing_service()
    assert service2 is custom_service

def test_empty_content():
    """Test hashing empty content."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA256))
    hash_str = service.hash_content(b"")
    assert len(hash_str) == 64  # Should still produce valid hash

def test_large_content():
    """Test hashing large content."""
    service = DefaultHashingService(HashingSettings(algorithm=HashFunction.SHA256))
    large_content = b"x" * 1024 * 1024  # 1MB of data
    hash_str = service.hash_content(large_content)
    assert len(hash_str) == 64  # Should handle large content
