"""
Tests for MCard domain exceptions.
"""
import pytest
from mcard.domain.models.exceptions import (
    MCardError,
    ValidationError,
    StorageError,
    HashingError,
    ConfigurationError
)

def test_mcarderror_is_exception():
    """Test that MCardError is a subclass of Exception."""
    assert issubclass(MCardError, Exception)

def test_validation_error_inheritance():
    """Test that ValidationError inherits from MCardError."""
    assert issubclass(ValidationError, MCardError)
    
    # Test instantiation and message
    error = ValidationError("Invalid data")
    assert str(error) == "Invalid data"

def test_storage_error_inheritance():
    """Test that StorageError inherits from MCardError."""
    assert issubclass(StorageError, MCardError)
    
    # Test instantiation and message
    error = StorageError("Storage failed")
    assert str(error) == "Storage failed"

def test_hashing_error_inheritance():
    """Test that HashingError inherits from MCardError."""
    assert issubclass(HashingError, MCardError)
    
    # Test instantiation and message
    error = HashingError("Hashing failed")
    assert str(error) == "Hashing failed"

def test_configuration_error_inheritance():
    """Test that ConfigurationError inherits from MCardError."""
    assert issubclass(ConfigurationError, MCardError)
    
    # Test instantiation and message
    error = ConfigurationError("Invalid configuration")
    assert str(error) == "Invalid configuration"

def test_error_handling():
    """Test that errors can be caught as both their specific type and as MCardError."""
    try:
        raise ValidationError("test error")
    except ValidationError as e:
        assert str(e) == "test error"
    except Exception:
        pytest.fail("ValidationError not caught as ValidationError")

    try:
        raise ValidationError("test error")
    except MCardError as e:
        assert str(e) == "test error"
    except Exception:
        pytest.fail("ValidationError not caught as MCardError")
