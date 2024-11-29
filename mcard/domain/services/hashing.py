"""
Comprehensive hashing service implementation.
"""
import hashlib
import importlib
from dataclasses import dataclass, field
from typing import Optional, Union, Callable, Any, Dict

from ..models.config import HashingSettings
from ..models.protocols import HashingService as HashingServiceProtocol

class HashingError(Exception):
    """Raised when hashing operations fail."""
    pass

class DefaultHashingService(HashingServiceProtocol):
    """
    Default implementation of HashingService.
    Supports multiple hashing algorithms including custom hash functions.
    """
    def __init__(self, settings: HashingSettings):
        """
        Initialize the hashing service with configuration.
        
        Args:
            settings: Hashing configuration settings
        """
        self.settings = settings
        self._hash_func = self._create_hash_function()
        self._hash_length = {
            "md5": 32,
            "sha1": 40,
            "sha256": 64,
            "sha512": 128,
            "custom": self.settings.custom_hash_length
        }.get(self.settings.algorithm)
        self.store = None  # Default to None

    def _create_hash_function(self) -> Union[Any, Callable[[bytes], str]]:
        """
        Get the appropriate hash function based on configuration.
        
        Returns:
            A function that takes bytes and returns a hash string
        """
        if self.settings.algorithm == "custom":
            if not self.settings.custom_module or not self.settings.custom_function:
                raise HashingError("Custom module and function must be specified")

            try:
                module = importlib.import_module(self.settings.custom_module)
                hash_func = getattr(module, self.settings.custom_function)
                return hash_func()  # Call factory function to get hash function
            except (ImportError, AttributeError) as e:
                raise HashingError(f"Failed to load custom hash function: {e}")

        # Use hashlib functions
        if self.settings.algorithm == "md5":
            return lambda content: hashlib.md5(content).hexdigest()
        elif self.settings.algorithm == "sha1":
            return lambda content: hashlib.sha1(content).hexdigest()
        elif self.settings.algorithm == "sha256":
            return lambda content: hashlib.sha256(content).hexdigest()
        elif self.settings.algorithm == "sha512":
            return lambda content: hashlib.sha512(content).hexdigest()
        else:
            raise HashingError(f"Unsupported hashing algorithm: {self.settings.algorithm}")

    async def async_hash_content(self, content: bytes) -> str:
        """Hash content and check for collisions."""
        if not content:
            raise HashingError("Cannot hash empty content")

        # First try with current algorithm
        hash_str = self._hash_func(content)

        if self.store:
            # Check for collision in store
            existing_card = await self.store.get(hash_str)
            if existing_card and existing_card.content != content:
                # Collision detected, upgrade algorithm
                await self._handle_collision(content, existing_card.content)
                # Compute hash with new algorithm
                return self._hash_func(content)

        return hash_str

    async def hash_content(self, content: bytes) -> str:
        """Wrapper method to ensure async behavior for hash_content."""
        return await self.async_hash_content(content)

    async def validate_hash(self, content: bytes, hash_str: str) -> bool:
        """Validate a hash string asynchronously."""
        # If no hash is provided, return False
        if not hash_str:
            return False

        # Validate hash length matches the expected length
        if len(hash_str) != self._hash_length:
            return False

        # Validate hash format (hexadecimal)
        try:
            int(hash_str, 16)
        except ValueError:
            return False

        # If content is provided, verify the hash matches the content
        if content:
            computed_hash = await self.hash_content(content)
            return computed_hash == hash_str

        return True

    async def async_validate_hash(self, hash_str: str) -> bool:
        """Async method to validate a hash string."""
        # If no hash is provided, return False
        if not hash_str:
            return False

        # Validate hash length matches the expected length
        if len(hash_str) != self._hash_length:
            return False

        # Validate hash format (hexadecimal)
        try:
            int(hash_str, 16)
            return True
        except ValueError:
            return False

class CollisionAwareHashingService(DefaultHashingService):
    """A hashing service that automatically upgrades the hashing algorithm when collisions are detected."""

    def __init__(self, settings: HashingSettings, repository = None):
        """Initialize the service with the given settings and optional repository."""
        super().__init__(settings)
        self._algorithm_hierarchy = ["md5", "sha1", "sha256", "sha512"]
        self.repository = repository

    async def store_collision(self, content1: bytes, content2: bytes, algorithm: str) -> None:
        """Store a known collision for the given algorithm."""
        if algorithm.lower() == self.settings.algorithm.lower():
            await self._handle_collision(content1, content2)

    async def _handle_collision(self, content1: bytes, content2: bytes) -> None:
        """Handle a collision by upgrading to the next strongest algorithm."""
        current_algo = self.settings.algorithm.lower()
        try:
            current_index = self._algorithm_hierarchy.index(current_algo)
            if current_index < len(self._algorithm_hierarchy) - 1:
                next_algo = self._algorithm_hierarchy[current_index + 1]
                self.settings.algorithm = next_algo
                self._hash_func = self._create_hash_function()
                self._hash_length = {
                    "md5": 32,
                    "sha1": 40,
                    "sha256": 64,
                    "sha512": 128,
                    "custom": self.settings.custom_hash_length
                }.get(self.settings.algorithm)
        except ValueError:
            # If current algorithm is not in hierarchy, default to strongest
            self.settings.algorithm = self._algorithm_hierarchy[-1]
            self._hash_func = self._create_hash_function()
            self._hash_length = {
                "md5": 32,
                "sha1": 40,
                "sha256": 64,
                "sha512": 128,
                "custom": self.settings.custom_hash_length
            }.get(self.settings.algorithm)

    async def async_hash_content(self, content: bytes) -> str:
        """Hash content and check for collisions."""
        if not content:
            raise HashingError("Cannot hash empty content")

        # First try with current algorithm
        hash_str = self._hash_func(content)

        if self.repository:
            # Check for collision in repository
            existing_card = await self.repository.get(hash_str)
            if existing_card and existing_card.content != content:
                # Collision detected, upgrade algorithm
                await self._handle_collision(content, existing_card.content)
                # Compute hash with new algorithm
                return self._hash_func(content)

        return hash_str

# Global default service
_default_service: Optional[DefaultHashingService] = None

def get_hashing_service(settings: Optional[HashingSettings] = None) -> DefaultHashingService:
    """
    Get or create a global default hashing service.
    
    Args:
        settings: Optional hashing settings. If not provided, default settings will be used.
    
    Returns:
        The default hashing service
    """
    global _default_service
    if _default_service is None or settings is not None:
        # Create a new service with provided or default settings
        service_settings = settings or HashingSettings()
        _default_service = DefaultHashingService(service_settings)
    return _default_service

def set_hashing_service(service: Optional[DefaultHashingService]) -> None:
    """
    Set the global hashing service instance.
    
    Args:
        service: Hashing service to set as global default
    """
    global _default_service
    _default_service = service
