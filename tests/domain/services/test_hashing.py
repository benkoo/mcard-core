"""
Tests for hashing service implementation.
"""
import pytest
from mcard.domain.services.hashing import (
    DefaultHashingService,
    CollisionAwareHashingService,
    get_hashing_service,
    set_hashing_service,
)
from mcard.domain.models.config import HashingSettings
from mcard.domain.models.exceptions import HashingError
from mcard.domain.models.card import MCard

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
    hash_str = "a" * 64
    assert default_service.validate_hash(hash_str)

@pytest.mark.asyncio
async def test_validate_hash_invalid_length(default_service):
    """Test hash validation with invalid length."""
    hash_str = "a" * 32
    assert not default_service.validate_hash(hash_str)

@pytest.mark.asyncio
async def test_validate_hash_invalid_chars(default_service):
    """Test hash validation with invalid characters."""
    hash_str = "x" * 64
    assert not default_service.validate_hash(hash_str)

@pytest.mark.asyncio
async def test_custom_hash_function_missing_settings():
    """Test custom hash function with missing settings."""
    settings = HashingSettings(algorithm="custom")
    with pytest.raises(HashingError, match="Custom hash function requires module and function names"):
        DefaultHashingService(settings)

@pytest.mark.asyncio
async def test_custom_hash_function_invalid_module():
    """Test custom hash function with invalid module."""
    settings = HashingSettings(
        algorithm="custom",
        custom_module="invalid_module",
        custom_function="invalid_function",
        custom_hash_length=32
    )
    with pytest.raises(HashingError, match="Failed to load custom hash function"):
        DefaultHashingService(settings)

@pytest.mark.asyncio
async def test_global_service_instance():
    """Test global service instance management."""
    # Reset global instance
    set_hashing_service(None)
    
    # Get default instance
    service1 = get_hashing_service()
    assert isinstance(service1, DefaultHashingService)
    assert service1.get_hash_length() == 64  # SHA256
    
    # Set custom instance
    custom_service = DefaultHashingService(HashingSettings(algorithm="sha512"))
    set_hashing_service(custom_service)
    
    # Verify custom instance is returned
    service2 = get_hashing_service()
    assert service2 is custom_service
    assert service2.get_hash_length() == 128  # SHA512

@pytest.mark.asyncio
async def test_empty_content(default_service):
    """Test hashing empty content."""
    with pytest.raises(HashingError, match="Cannot hash empty content"):
        await default_service.hash_content(b"")

@pytest.mark.asyncio
async def test_large_content():
    """Test hashing large content."""
    service = DefaultHashingService(HashingSettings(algorithm="sha256"))
    content = b"x" * 1000000  # 1MB of data
    hash_str = await service.hash_content(content)
    assert len(hash_str) == 64
    assert all(c in '0123456789abcdef' for c in hash_str)

@pytest.mark.asyncio
async def test_collision_aware_service():
    """Test CollisionAwareHashingService behavior."""
    service = CollisionAwareHashingService(HashingSettings(algorithm="sha256"))
    content = b"test content"
    hash_str = await service.hash_content(content)
    assert len(hash_str) == 64

@pytest.mark.asyncio
async def test_collision_aware_upgrade():
    """Test that CollisionAwareHashingService upgrades algorithm on collision."""
    service = CollisionAwareHashingService(HashingSettings(algorithm="md5"))

    # Simulate collision detection
    content1 = b"content1"
    content2 = b"content2"
    await service._handle_collision(content1, content2)

    # Verify upgrade to SHA1
    assert service._settings.algorithm == "sha1"

@pytest.mark.asyncio
async def test_collision_aware_service_md5():
    """Test that CollisionAwareHashingService automatically upgrades from MD5 when collision is detected."""
    service = CollisionAwareHashingService(HashingSettings(algorithm="md5"))

    # Store known MD5 collision
    message1 = bytes.fromhex('d131dd02c5e6eec4693d9a0698aff95c2fcab58712467eab4004583eb8fb7f8955ad340609f4b30283e488832571415a085125e8f7cdc99fd91dbdf280373c5bd8823e3156348f5bae6dacd436c919c6dd53e2b487da03fd02396306d248cda0e99f33420f577ee8ce54b67080a80d1ec69821bcb6a8839396f9652b6ff72a70')
    message2 = bytes.fromhex('d131dd02c5e6eec4693d9a0698aff95c2fcab50712467eab4004583eb8fb7f8955ad340609f4b30283e4888325f1415a085125e8f7cdc99fd91dbd7280373c5bd8823e3156348f5bae6dacd436c919c6dd53e23487da03fd02396306d248cda0e99f33420f577ee8ce54b67080280d1ec69821bcb6a8839396f965ab6ff72a70')

    await service.store_collision(message1, message2, "md5")

    # First hash should use MD5
    hash1 = await service.hash_content(message1)
    assert service._settings.algorithm == "sha1"  # Should upgrade to SHA1

@pytest.mark.asyncio
async def test_collision_aware_service_sha1():
    """Test that CollisionAwareHashingService automatically upgrades from SHA1 when collision is detected."""
    service = CollisionAwareHashingService(HashingSettings(algorithm="sha1"))

    # Store known SHA1 collision from SHAttered attack
    pdf1_prefix = bytes.fromhex('255044462D312E330A25E2E3CFD30A0A0A312030206F626A0A3C3C2F57696474682032203020522F4865696768742033203020522F547970652034203020522F537562747970652035203020522F46696C7465722036203020522F436F6C6F7253706163652037203020522F4C656E6774682038203020522F42697473506572436F6D706F6E656E7420383E3E0A73747265616D0AFFD8FFFE00245348412D3120697320646561642121212121852FEC092339759C39B1A1C63C4C97E1FFFE017F46DC93A6B67E013B029AAA1DB2560B45CA67D688C7F84B8C4C791FE02B3DF614F86DB1690901C56B45C1530AFEDFB76038E972722FE7AD728F0E4904E046C230570FE9D41398ABE12EF5BC942BE33542A4802D98B5D70F2A332EC37FAC3514E74DDC0F2CC1A874CD0C78305A21566461309789606BD0BF3F98CDA8044629A1')
    pdf2_prefix = bytes.fromhex('255044462D312E330A25E2E3CFD30A0A0A312030206F626A0A3C3C2F57696474682032203020522F4865696768742033203020522F547970652034203020522F537562747970652035203020522F46696C7465722036203020522F436F6C6F7253706163652037203020522F4C656E6774682038203020522F42697473506572436F6D706F6E656E7420383E3E0A73747265616D0AFFD8FFFE00245348412D3120697320646561642121212121852FEC092339759C39B1A1C63C4C97E1FFFE017346DC9166B67E118F029AB621B2560FF9CA67CCA8C7F85BA84C79030C2B3DE218F86DB3A90901D5DF45C14F26FEDFB3DC38E96AC22FE7BD728F0E45BCE046D23C570FEB141398BB552EF5A0A82BE331FEA48037B8B5D71F0E332EDF93AC3500EB4DDC0DECC1A864790C782C76215660DD309791D06BD0AF3F98CDA4BC4629B1')

    await service.store_collision(pdf1_prefix, pdf2_prefix, "sha1")

    # First hash should use SHA1
    hash1 = await service.hash_content(pdf1_prefix)
    assert service._settings.algorithm == "sha256"  # Should upgrade to SHA256

@pytest.mark.asyncio
async def test_collision_aware_service_with_repository():
    """Test CollisionAwareHashingService with a repository for collision detection."""
    # Create a mock repository that tracks access
    class MockRepository:
        def __init__(self):
            self.get_called = False
            
        async def get(self, hash_str):
            if not self.get_called and hash_str == "79054025255fb1a26e4bc422aef54eb4":  # Known MD5 collision hash
                self.get_called = True  # Prevent infinite recursion
                return MCard(
                    content=bytes.fromhex('d131dd02c5e6eec4693d9a0698aff95c2fcab58712467eab4004583eb8fb7f8955ad340609f4b30283e488832571415a085125e8f7cdc99fd91dbdf280373c5bd8823e3156348f5bae6dacd436c919c6dd53e2b487da03fd02396306d248cda0e99f33420f577ee8ce54b67080a80d1ec69821bcb6a8839396f9652b6ff72a70')
                )
            return None

    mock_repo = MockRepository()
    service = CollisionAwareHashingService(
        HashingSettings(algorithm="md5"),
        card_repository=mock_repo
    )

    # Try to hash the colliding message
    message2 = bytes.fromhex('d131dd02c5e6eec4693d9a0698aff95c2fcab50712467eab4004583eb8fb7f8955ad340609f4b30283e4888325f1415a085125e8f7cdc99fd91dbd7280373c5bd8823e3156348f5bae6dacd436c919c6dd53e23487da03fd02396306d248cda0e99f33420f577ee8ce54b67080280d1ec69821bcb6a8839396f965ab6ff72a70')

    # Should detect collision from repository and upgrade
    hash2 = await service.hash_content(message2)
    assert service._settings.algorithm == "sha1"  # Should upgrade to SHA1
    assert hash2 != "79054025255fb1a26e4bc422aef54eb4"  # Should not use MD5 hash
    assert mock_repo.get_called  # Verify repository was queried

@pytest.mark.asyncio
async def test_md5_collision():
    """Test MD5 collision vulnerability using known collision examples."""
    service = DefaultHashingService(HashingSettings(algorithm="md5"))

    # These two hex strings are known to produce the same MD5 hash
    # Source: https://www.mscs.dal.ca/~selinger/md5collision/
    message1 = bytes.fromhex('d131dd02c5e6eec4693d9a0698aff95c2fcab58712467eab4004583eb8fb7f8955ad340609f4b30283e488832571415a085125e8f7cdc99fd91dbdf280373c5bd8823e3156348f5bae6dacd436c919c6dd53e2b487da03fd02396306d248cda0e99f33420f577ee8ce54b67080a80d1ec69821bcb6a8839396f9652b6ff72a70')
    message2 = bytes.fromhex('d131dd02c5e6eec4693d9a0698aff95c2fcab50712467eab4004583eb8fb7f8955ad340609f4b30283e4888325f1415a085125e8f7cdc99fd91dbd7280373c5bd8823e3156348f5bae6dacd436c919c6dd53e23487da03fd02396306d248cda0e99f33420f577ee8ce54b67080280d1ec69821bcb6a8839396f965ab6ff72a70')

    hash1 = await service.hash_content(message1)
    hash2 = await service.hash_content(message2)

    # Despite being different messages, they should produce the same MD5 hash
    assert message1 != message2, "Test messages should be different"
    assert hash1 == hash2, "MD5 collision pair should produce the same hash"
    assert hash1 == "79054025255fb1a26e4bc422aef54eb4"  # Known collision hash

@pytest.mark.asyncio
async def test_sha1_collision():
    """Test SHA-1 collision vulnerability using known collision examples from the SHAttered attack."""
    service = DefaultHashingService(HashingSettings(algorithm="sha1"))

    # These are the first 320 bytes of the two PDF files from the SHAttered attack
    # The complete files can be found at https://shattered.io/
    pdf1_prefix = bytes.fromhex('255044462D312E330A25E2E3CFD30A0A0A312030206F626A0A3C3C2F57696474682032203020522F4865696768742033203020522F547970652034203020522F537562747970652035203020522F46696C7465722036203020522F436F6C6F7253706163652037203020522F4C656E6774682038203020522F42697473506572436F6D706F6E656E7420383E3E0A73747265616D0AFFD8FFFE00245348412D3120697320646561642121212121852FEC092339759C39B1A1C63C4C97E1FFFE017F46DC93A6B67E013B029AAA1DB2560B45CA67D688C7F84B8C4C791FE02B3DF614F86DB1690901C56B45C1530AFEDFB76038E972722FE7AD728F0E4904E046C230570FE9D41398ABE12EF5BC942BE33542A4802D98B5D70F2A332EC37FAC3514E74DDC0F2CC1A874CD0C78305A21566461309789606BD0BF3F98CDA8044629A1')
    pdf2_prefix = bytes.fromhex('255044462D312E330A25E2E3CFD30A0A0A312030206F626A0A3C3C2F57696474682032203020522F4865696768742033203020522F547970652034203020522F537562747970652035203020522F46696C7465722036203020522F436F6C6F7253706163652037203020522F4C656E6774682038203020522F42697473506572436F6D706F6E656E7420383E3E0A73747265616D0AFFD8FFFE00245348412D3120697320646561642121212121852FEC092339759C39B1A1C63C4C97E1FFFE017346DC9166B67E118F029AB621B2560FF9CA67CCA8C7F85BA84C79030C2B3DE218F86DB3A90901D5DF45C14F26FEDFB3DC38E96AC22FE7BD728F0E45BCE046D23C570FEB141398BB552EF5A0A82BE331FEA48037B8B5D71F0E332EDF93AC3500EB4DDC0DECC1A864790C782C76215660DD309791D06BD0AF3F98CDA4BC4629B1')

    hash1 = await service.hash_content(pdf1_prefix)
    hash2 = await service.hash_content(pdf2_prefix)

    # Verify the collision
    assert pdf1_prefix != pdf2_prefix, "Test messages should be different"
    assert hash1 == hash2, "SHA-1 collision pair should produce the same hash"
    assert hash1 == "f92d74e3874587aaf443d1db961d4e26dde13e9c"  # Known collision hash
