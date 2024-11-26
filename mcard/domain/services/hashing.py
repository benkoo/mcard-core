"""
Hashing service implementation.
"""
import hashlib
import importlib
from typing import Optional, Callable
from ..models.config import HashFunction, HashingSettings
from ..models.exceptions import HashingError

class DefaultHashingService:
    """Default implementation of hashing service."""
    _instance = None
    _hash_lengths = {
        HashFunction.SHA256: 64,
        HashFunction.SHA512: 128,
        HashFunction.SHA1: 40,
        HashFunction.MD5: 32,
    }

    def __init__(self, settings: Optional[HashingSettings] = None):
        self._settings = settings or HashingSettings()
        self._custom_hash_function: Optional[Callable[[bytes], str]] = None
        self._initialize_hash_function()

    def _initialize_hash_function(self) -> None:
        """Initialize the hash function based on settings."""
        if self._settings.algorithm == HashFunction.CUSTOM:
            if not all([
                self._settings.custom_module,
                self._settings.custom_function,
                self._settings.custom_hash_length
            ]):
                raise HashingError(
                    "Custom hash function requires module, function name, and hash length"
                )
            try:
                module = importlib.import_module(self._settings.custom_module)
                self._custom_hash_function = getattr(module, self._settings.custom_function)
            except (ImportError, AttributeError) as e:
                raise HashingError(f"Failed to load custom hash function: {str(e)}")

    def hash_content(self, content: bytes) -> str:
        """Hash the given content."""
        if self._settings.algorithm == HashFunction.CUSTOM:
            if not self._custom_hash_function:
                raise HashingError("Custom hash function not initialized")
            try:
                result = self._custom_hash_function(content)
                if not isinstance(result, str):
                    raise HashingError("Custom hash function must return a string")
                if len(result) != self._settings.custom_hash_length:
                    raise HashingError(
                        f"Custom hash length mismatch. Expected {self._settings.custom_hash_length}, got {len(result)}"
                    )
                return result
            except Exception as e:
                raise HashingError(f"Custom hash function failed: {str(e)}")
        else:
            hasher = hashlib.new(self._settings.algorithm)
            hasher.update(content)
            return hasher.hexdigest()

    def validate_hash(self, hash_str: str) -> bool:
        """Validate a hash string."""
        if self._settings.algorithm == HashFunction.CUSTOM:
            return (
                isinstance(hash_str, str) and
                len(hash_str) == self._settings.custom_hash_length
            )
        else:
            expected_length = self._hash_lengths.get(self._settings.algorithm)
            return (
                isinstance(hash_str, str) and
                len(hash_str) == expected_length and
                all(c in '0123456789abcdef' for c in hash_str.lower())
            )

    @classmethod
    def get_instance(cls) -> 'DefaultHashingService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Global instance
_default_service = None

def get_hashing_service() -> DefaultHashingService:
    """Get the global hashing service instance."""
    global _default_service
    if _default_service is None:
        _default_service = DefaultHashingService()
    return _default_service

def set_hashing_service(service: DefaultHashingService) -> None:
    """Set the global hashing service instance."""
    global _default_service
    _default_service = service
