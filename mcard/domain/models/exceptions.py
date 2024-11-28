"""
MCard domain exceptions.
"""

class MCardError(Exception):
    """Base exception for MCard operations."""
    pass

class ValidationError(MCardError):
    """Validation related errors."""
    pass

class StorageError(MCardError):
    """Storage related errors."""
    pass

class HashingError(MCardError):
    """Hashing related errors."""
    pass

class ConfigurationError(MCardError):
    """Configuration related errors."""
    pass
