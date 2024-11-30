"""
Tests for hashing service implementation.
"""
import pytest
from mcard.domain.services.hashing import (
    DefaultHashingService,
    get_hashing_service,
    set_hashing_service,
)
from mcard.domain.models.config import HashingSettings
from mcard.domain.models.exceptions import HashingError
from mcard.domain.models.card import MCard
import re

def validate_error_message(expected_message):
    """Helper function to validate error messages."""
    def _validate(exc_info):
        assert str(exc_info.value) == expected_message, f"Expected error message '{expected_message}', got '{str(exc_info.value)}'"
    return _validate

@pytest.fixture
def default_service():
    """Create a default hashing service with SHA256."""
    settings = HashingSettings(algorithm="sha256")
    return DefaultHashingService(settings)

@pytest.mark.asyncio
async def test_hash_content_sha256(default_service):
    """Test hashing with SHA256."""
    content = b"test content"
    hash_str = await default_service.hash_content(content)
    assert len(hash_str) == 64
    assert all(c in '0123456789abcdef' for c in hash_str)
    assert hash_str == "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"

@pytest.mark.asyncio
async def test_hash_content_sha512():
    """Test hashing with SHA512."""
    service = DefaultHashingService(HashingSettings(algorithm="sha512"))
    content = b"test content"
    hash_str = await service.hash_content(content)
    assert len(hash_str) == 128
    assert all(c in '0123456789abcdef' for c in hash_str)

@pytest.mark.asyncio
async def test_hash_content_sha1():
    """Test hashing with SHA1."""
    service = DefaultHashingService(HashingSettings(algorithm="sha1"))
    content = b"test content"
    hash_str = await service.hash_content(content)
    assert len(hash_str) == 40
    assert all(c in '0123456789abcdef' for c in hash_str)

@pytest.mark.asyncio
async def test_hash_content_md5():
    """Test hashing with MD5."""
    service = DefaultHashingService(HashingSettings(algorithm="md5"))
    content = b"test content"
    hash_str = await service.hash_content(content)
    assert len(hash_str) == 32
    assert all(c in '0123456789abcdef' for c in hash_str)

@pytest.mark.asyncio
async def test_validate_hash_valid(default_service):
    """Test hash validation with valid hash."""
    hash_str = "a" * 64  # Valid SHA256 length
    assert await default_service.validate_hash(hash_str)

@pytest.mark.asyncio
async def test_validate_hash_invalid_length(default_service):
    """Test hash validation with invalid length."""
    hash_str = "a" * 32  # Invalid length for SHA256
    assert not await default_service.validate_hash(hash_str)

@pytest.mark.asyncio
async def test_global_service_instance():
    """Test global service instance management."""
    # Get default service
    service1 = get_hashing_service()
    assert service1 is not None
    
    # Get another reference - should be same instance
    service2 = get_hashing_service()
    assert service2 is service1
    
    # Set new service
    new_settings = HashingSettings(algorithm="sha512")
    new_service = DefaultHashingService(new_settings)
    set_hashing_service(new_service)
    
    # Get service - should be new instance
    service3 = get_hashing_service()
    assert service3 is new_service
    assert service3 is not service1

@pytest.mark.asyncio
async def test_next_level_hash():
    """Test next level hash progression."""
    # Test MD5 to SHA1
    md5_service = DefaultHashingService(HashingSettings(algorithm="md5"))
    sha1_service = await md5_service.next_level_hash()
    assert sha1_service.settings.algorithm == "sha1"
    
    # Test SHA1 to SHA256
    sha256_service = await sha1_service.next_level_hash()
    assert sha256_service.settings.algorithm == "sha256"
    
    # Test SHA256 to SHA384
    sha384_service = await sha256_service.next_level_hash()
    assert sha384_service.settings.algorithm == "sha384"
    
    # Test SHA384 to SHA512
    sha512_service = await sha384_service.next_level_hash()
    assert sha512_service.settings.algorithm == "sha512"
    
    # Test SHA512 to custom
    custom_service = await sha512_service.next_level_hash()
    assert custom_service.settings.algorithm == "custom"
    
    # Test custom to error
    with pytest.raises(HashingError) as exc_info:
        await custom_service.next_level_hash()
    assert "No stronger hashing algorithm available" in str(exc_info.value)

@pytest.mark.asyncio
async def test_large_content():
    """Test hashing large content."""
    service = DefaultHashingService(HashingSettings(algorithm="sha256"))
    content = b"x" * 1024 * 1024  # 1MB of data
    hash_str = await service.hash_content(content)
    assert len(hash_str) == 64
    assert all(c in '0123456789abcdef' for c in hash_str)
