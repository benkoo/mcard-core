"""
MCard: A wrapper class for content-addressable data.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional, Dict, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import hashlib
import time


def get_now_with_located_zone() -> datetime:
    """
    Get current time with the local timezone. Always ensures timezone information is present.
    Returns time with local timezone.
    """
    return datetime.now().astimezone()


class HashFunction(Enum):
    """Supported hash functions."""
    SHA256 = "sha256"
    SHA512 = "sha512"
    SHA1 = "sha1"
    MD5 = "md5"  # Note: MD5 is not cryptographically secure, included for compatibility
    CUSTOM = "custom"


class HashingConfig:
    """Configuration for content hashing."""
    _instance = None
    _hash_lengths = {
        HashFunction.SHA256: 64,
        HashFunction.SHA512: 128,
        HashFunction.SHA1: 40,
        HashFunction.MD5: 32,
        HashFunction.CUSTOM: None  # Length will be determined from the custom function
    }

    def __init__(self):
        self._hash_function = HashFunction.SHA256
        self._custom_hash_function: Optional[Callable[[bytes], str]] = None
        self._custom_hash_length: Optional[int] = None

    @classmethod
    def get_instance(cls) -> 'HashingConfig':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def hash_function(self) -> HashFunction:
        """Get current hash function."""
        return self._hash_function

    def set_custom_hash_function(self, func: Callable[[bytes], str], expected_length: int):
        """
        Set a custom hash function.
        
        Args:
            func: Function that takes bytes and returns a hex string hash
            expected_length: Expected length of the hash string
        """
        # Validate the function
        test_input = b"test"
        try:
            result = func(test_input)
            if not isinstance(result, str):
                raise ValueError("Custom hash function must return a string")
            try:
                int(result, 16)
            except ValueError:
                raise ValueError("Custom hash function must return a valid hex string")
        except Exception as e:
            raise ValueError(f"Invalid custom hash function: {str(e)}")

        self._custom_hash_function = func
        self._custom_hash_length = expected_length
        self._hash_lengths[HashFunction.CUSTOM] = expected_length
        self._hash_function = HashFunction.CUSTOM

    @hash_function.setter
    def hash_function(self, value: HashFunction):
        """Set hash function."""
        if not isinstance(value, HashFunction):
            raise ValueError("Hash function must be a HashFunction enum value")
        if value == HashFunction.CUSTOM and self._custom_hash_function is None:
            raise ValueError("Custom hash function not set. Use set_custom_hash_function first.")
        self._hash_function = value

    def get_hash_length(self) -> int:
        """Get expected hash length for current function."""
        length = self._hash_lengths[self._hash_function]
        if length is None:
            raise ValueError("Hash length not set for custom function")
        return length

    def compute_hash(self, content: bytes) -> str:
        """Compute hash of content using configured function."""
        if self._hash_function == HashFunction.CUSTOM:
            if self._custom_hash_function is None:
                raise ValueError("Custom hash function not set")
            return self._custom_hash_function(content)
        else:
            hasher = hashlib.new(self._hash_function.value)
            hasher.update(content)
            return hasher.hexdigest()


class MCard(BaseModel):
    """
    A wrapper class for content-addressable data.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='forbid'
    )

    content: Any = Field(description="The actual content of the MCard.")
    content_hash: str = Field(description="Hash of the content using configured hash function. This is automatically calculated from the content.", default=None, frozen=True)
    time_claimed: datetime = Field(
        default_factory=get_now_with_located_zone,
        description="Timestamp when the content was claimed."
    )

    @model_validator(mode='before')
    def calculate_content_hash(cls, values):
        """Calculate content hash if not provided."""
        if 'content' in values and ('content_hash' not in values or values['content_hash'] is None):
            content = values['content']
            if isinstance(content, str):
                content = content.encode('utf-8')
            elif not isinstance(content, bytes):
                content = str(content).encode('utf-8')
            
            hashing_config = HashingConfig.get_instance()
            values['content_hash'] = hashing_config.compute_hash(content)
        return values

    @field_validator('content_hash')
    def validate_content_hash(cls, v: str) -> str:
        """Validate content_hash format."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("content_hash must be a string")
        
        hashing_config = HashingConfig.get_instance()
        expected_length = hashing_config.get_hash_length()
        
        if len(v) != expected_length:
            raise ValueError(f"content_hash must be a {expected_length}-character hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("content_hash must be a valid hex string")
        return v.lower()

    @field_validator('time_claimed')
    def validate_time_claimed(cls, v: datetime) -> datetime:
        """Ensure time_claimed has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    def __str__(self) -> str:
        """String representation of MCard."""
        return f"MCard(content_hash={self.content_hash})"
