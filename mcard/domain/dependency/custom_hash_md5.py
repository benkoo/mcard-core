"""
Custom hash function implementation using MD5.
This is for demonstration purposes only - MD5 is not recommended for security-critical applications.
"""
import hashlib
from typing import Callable

def create_md5_hasher() -> Callable[[bytes], str]:
    """
    Create an MD5 hash function that follows the HashingService interface.
    
    Returns:
        Callable[[bytes], str]: A function that takes bytes and returns a hex string
    """
    def md5_hash(content: bytes) -> str:
        """
        Hash content using MD5.
        
        Args:
            content: The bytes to hash
            
        Returns:
            str: The hexadecimal representation of the MD5 hash
            
        Note:
            This is just a demonstration. MD5 is cryptographically broken and should not
            be used in security-critical applications. Use SHA-256 or stronger instead.
        """
        if not isinstance(content, bytes):
            raise TypeError("Content must be bytes")
        
        if not content:
            raise ValueError("Cannot hash empty content")
        
        # Create MD5 hash object
        hash_obj = hashlib.md5()
        
        # Update with content
        hash_obj.update(content)
        
        # Return hexadecimal representation
        return hash_obj.hexdigest()
    
    return md5_hash

# For backwards compatibility
custom_md5_hash = create_md5_hasher()
