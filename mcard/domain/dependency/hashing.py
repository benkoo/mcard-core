"""
Simplified hashing service implementation.
"""
import hashlib
import importlib
from dataclasses import dataclass
from typing import Optional, Union, Callable, Any

@dataclass
class HashingSettings:
    """Settings for content hashing."""
    algorithm: str = "sha256"
    custom_module: Optional[str] = None
    custom_function: Optional[str] = None
    custom_hash_length: Optional[int] = None

class HashingError(Exception):
    """Raised when hashing operations fail."""
    pass

class HashingService:
    """Base hashing service implementation."""

    # Standard hash algorithms and their output lengths
    STANDARD_ALGORITHMS = {
        "md5": 32,
        "sha1": 40,
        "sha256": 64,
        "sha512": 128,
    }
    
    def __init__(self, settings: Optional[HashingSettings] = None):
        """Initialize with settings."""
        self.settings = settings or HashingSettings()
        self._hash_func = self._create_hash_function()
    
    def _create_hash_function(self) -> Union[Any, Callable[[bytes], str]]:
        """Create hash function based on settings."""
        if self.settings.algorithm == "custom":
            if not self.settings.custom_module or not self.settings.custom_function:
                raise HashingError("Custom module and function must be specified")
            
            try:
                module = importlib.import_module(self.settings.custom_module)
                hash_func = getattr(module, self.settings.custom_function)
                return hash_func()  # Call factory function to get hash function
            except (ImportError, AttributeError) as e:
                raise HashingError(f"Failed to load custom hash function: {e}")
        
        if self.settings.algorithm not in self.STANDARD_ALGORITHMS:
            raise HashingError(f"Unsupported algorithm: {self.settings.algorithm}")
        
        return getattr(hashlib, self.settings.algorithm)
    
    def hash_content(self, content: bytes) -> str:
        """Hash the given content."""
        if not content:
            raise HashingError("Cannot hash empty content")
    
        # Handle both hashlib-style objects and direct hash functions
        if hasattr(self._hash_func, "update"):
            # Hashlib-style object with update/hexdigest methods
            hash_obj = self._hash_func()
            hash_obj.update(content)
            hash_value = hash_obj.hexdigest()
        else:
            # Direct hash function that takes bytes and returns hex string
            hash_value = self._hash_func(content)
    
        # Validate hash length
        expected_length = (
            self.settings.custom_hash_length
            if self.settings.algorithm == "custom"
            else self.STANDARD_ALGORITHMS[self.settings.algorithm]
        )
    
        if isinstance(hash_value, str) and len(hash_value) != expected_length:
            raise HashingError(f"Hash length mismatch. Expected {expected_length}, got {len(hash_value)}")
        
        return hash_value if isinstance(hash_value, str) else hash_value.hexdigest()

# Global instance
_default_service = None

def get_hashing_service() -> Optional[HashingService]:
    """Get the global hashing service instance."""
    return _default_service

def set_hashing_service(service: Optional[HashingService]) -> None:
    """Set the global hashing service instance."""
    global _default_service
    _default_service = service
