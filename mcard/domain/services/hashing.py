"""
Hashing service implementation.
"""
import hashlib
import importlib
from typing import Optional, Dict

from ..models.config import HashingSettings
from ..models.exceptions import HashingError

# Expected hash lengths for each algorithm
HASH_LENGTHS = {
    "md5": 32,     # 128 bits -> 32 hex chars
    "sha1": 40,    # 160 bits -> 40 hex chars
    "sha256": 64,  # 256 bits -> 64 hex chars
    "sha512": 128  # 512 bits -> 128 hex chars
}

class DefaultHashingService:
    """Default implementation of the HashingService protocol."""

    def __init__(self, settings: HashingSettings):
        """Initialize with settings."""
        self._settings = settings
        self._hash_func = self._get_hash_function()

    def _get_hash_function(self):
        """Get the hash function based on settings."""
        if self._settings.algorithm == "custom":
            if not self._settings.custom_module or not self._settings.custom_function:
                raise HashingError("Custom hash function requires module and function names")
            try:
                module = importlib.import_module(self._settings.custom_module)
                return getattr(module, self._settings.custom_function)
            except (ImportError, AttributeError) as e:
                raise HashingError(f"Failed to load custom hash function: {e}")
        
        return getattr(hashlib, self._settings.algorithm)

    def hash_content_sync(self, content: bytes) -> str:
        """Hash the given content synchronously."""
        if not content:
            raise HashingError("Cannot hash empty content")
        
        hash_obj = self._hash_func()
        hash_obj.update(content)
        result = hash_obj.hexdigest()
        
        # Validate hash length for known algorithms
        if (expected_length := HASH_LENGTHS.get(self._settings.algorithm)):
            if len(result) != expected_length:
                raise HashingError(f"Invalid hash length: got {len(result)}, expected {expected_length}")
        elif self._settings.custom_hash_length:
            if len(result) != self._settings.custom_hash_length:
                raise HashingError(f"Invalid custom hash length: got {len(result)}, expected {self._settings.custom_hash_length}")
        
        return result

    async def hash_content(self, content: bytes) -> str:
        """Hash the given content."""
        return self.hash_content_sync(content)

    def validate_hash(self, hash_str: str) -> bool:
        """Validate a hash string."""
        if not isinstance(hash_str, str):
            return False

        if self._settings.algorithm == "custom":
            return len(hash_str) == self._settings.custom_hash_length
        else:
            expected_length = HASH_LENGTHS[self._settings.algorithm]
            return (
                len(hash_str) == expected_length and
                all(c in '0123456789abcdef' for c in hash_str.lower())
            )

    def verify_hash(self, content: bytes, hash_str: str) -> bool:
        """Verify that content matches a hash."""
        if not self.validate_hash(hash_str):
            return False
        return self.hash_content_sync(content) == hash_str

    def get_hash_length(self) -> int:
        """Get the expected length of hash strings."""
        if self._settings.algorithm == "custom":
            if not self._settings.custom_hash_length:
                raise HashingError("Custom hash length not set")
            return self._settings.custom_hash_length
        return HASH_LENGTHS[self._settings.algorithm]

# Global instance
_default_service = None

def get_hashing_service() -> DefaultHashingService:
    """Get the global hashing service instance."""
    global _default_service
    if _default_service is None:
        _default_service = DefaultHashingService(HashingSettings())
    return _default_service

def set_hashing_service(service: Optional[DefaultHashingService]) -> None:
    """Set the global hashing service instance."""
    global _default_service
    _default_service = service

class CollisionAwareHashingService(DefaultHashingService):
    """A hashing service that automatically upgrades to stronger algorithms when collisions are detected."""

    # Order of algorithm strength, from weakest to strongest
    ALGORITHM_STRENGTH = [
        "md5",
        "sha1",
        "sha256",
        "sha512"
    ]

    def __init__(self, settings: Optional[HashingSettings] = None, card_repository = None):
        """Initialize with settings and optional card repository for collision detection."""
        super().__init__(settings or HashingSettings())
        self._card_repository = card_repository
        self._collision_cache = {}  # Cache to store known collisions
        self._current_algorithm_index = self.ALGORITHM_STRENGTH.index(self._settings.algorithm)

    def _upgrade_algorithm(self):
        """Upgrade to the next stronger algorithm."""
        if self._current_algorithm_index < len(self.ALGORITHM_STRENGTH) - 1:
            self._current_algorithm_index += 1
            self._settings.algorithm = self.ALGORITHM_STRENGTH[self._current_algorithm_index]
            self._hash_func = self._get_hash_function()

    def _handle_collision(self, content1: bytes, content2: bytes):
        """Handle hash collision by upgrading to a stronger algorithm."""
        # Store collision in cache
        current_hash = super().hash_content_sync(content1)
        self._collision_cache[current_hash] = (content1, content2)
        
        # Upgrade to stronger algorithm
        self._upgrade_algorithm()

    def store_collision(self, content1: bytes, content2: bytes, algorithm: str):
        """Store a known collision case."""
        if algorithm not in self.ALGORITHM_STRENGTH:
            raise HashingError(f"Unsupported algorithm for collision tracking: {algorithm}")

        # Find the algorithm index and upgrade to the next stronger one
        try:
            current_index = self.ALGORITHM_STRENGTH.index(algorithm)
            if current_index >= self._current_algorithm_index:
                self._current_algorithm_index = current_index
                self._upgrade_algorithm()
        except ValueError:
            raise HashingError(f"Invalid algorithm: {algorithm}")

        # Store in collision cache
        current_hash = super().hash_content_sync(content1)
        self._collision_cache[current_hash] = (content1, content2)

    async def hash_content(self, content: bytes) -> str:
        """Hash content and check for collisions, upgrading algorithm if needed."""
        if not content:
            raise HashingError("Cannot hash empty content")

        # Check repository for collisions if available
        current_hash = await super().hash_content(content)
        if self._card_repository:
            existing_card = await self._card_repository.get(current_hash)
            if existing_card and existing_card.content != content:
                self._handle_collision(content, existing_card.content)
                return await self.hash_content(content)  # Retry with upgraded algorithm

        # Check collision cache
        if current_hash in self._collision_cache:
            stored_content1, stored_content2 = self._collision_cache[current_hash]
            if content != stored_content1 and content != stored_content2:
                self._handle_collision(content, stored_content1)
                return await self.hash_content(content)  # Retry with upgraded algorithm

        return current_hash
