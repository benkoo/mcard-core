"""Domain model exceptions."""

class ValidationError(Exception):
    """Raised when domain model validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass

class StorageError(Exception):
    """Raised when storage operations fail."""
    pass
