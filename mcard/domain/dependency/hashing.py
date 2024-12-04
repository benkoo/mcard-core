"""Hashing settings and utilities."""
import hashlib
import importlib
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class HashingSettings:
    """Configuration for hashing behavior."""
    algorithm: str = "sha256"
    custom_module: Optional[str] = None
    custom_function: Optional[str] = None
    custom_length: Optional[int] = None

    def get_hash_function(self) -> Callable[[bytes], str]:
        """Get the configured hash function.
        
        Returns:
            Callable[[bytes], str]: A function that takes bytes and returns a hash string
        """
        if self.algorithm == "custom":
            if not self.custom_module or not self.custom_function:
                raise ValueError("Custom hash algorithm requires both module and function names")
            try:
                module = importlib.import_module(self.custom_module)
                return getattr(module, self.custom_function)
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Failed to load custom hash function: {e}")
        
        try:
            hash_func = getattr(hashlib, self.algorithm)
            return lambda data: hash_func(data).hexdigest()
        except AttributeError:
            raise ValueError(f"Unsupported hash algorithm: {self.algorithm}")
