"""Domain model exceptions."""

class MCardError(Exception):
    """Base exception for all MCard errors."""
    pass

class ValidationError(MCardError):
    """Raised when domain model validation fails."""
    pass

class ConfigurationError(MCardError):
    """Raised when configuration validation fails."""
    pass

class StorageError(MCardError):
    """Raised when storage operations fail."""
    pass

class HashingError(MCardError):
    """Raised when hashing operations fail."""
    pass
