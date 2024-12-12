"""
Comprehensive hashing service implementation.
"""
import hashlib
import importlib
from dataclasses import dataclass, field
from typing import Optional, Union, Callable, Any, Dict
import logging

logger = logging.getLogger(__name__)

from mcard.domain.models.domain_config_models import HashingSettings
from mcard.domain.models.hashing_protocol import HashingService as HashingServiceProtocol

class HashingError(Exception):
    """Raised when hashing operations fail."""
    pass

class DefaultHashingService(HashingServiceProtocol):
    """
    Default implementation of HashingService.
    Supports multiple hashing algorithms including custom hash functions.
    """
    # Define algorithm hierarchy with strength ratings (higher is stronger)
    ALGORITHM_HIERARCHY = {
        'md5': 1,
        'sha1': 2,
        'sha224': 3,
        'sha256': 4,
        'sha384': 5,
        'sha512': 6,
        'custom': 7
    }
    
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
            "sha224": 56,
            "sha256": 64,
            "sha384": 96,
            "sha512": 128,
            "custom": self.settings.custom_hash_length
        }.get(self.settings.algorithm)
        
        # Validate algorithm is supported
        if self.settings.algorithm not in self.ALGORITHM_HIERARCHY:
            raise HashingError(f"Unsupported algorithm: {self.settings.algorithm}")
            
        self.store = None  # Default to None
        
        # Initialize parallel hashing if configured
        self._parallel_algorithms = settings.parallel_algorithms or []
        self._parallel_hash_funcs = {}
        if self._parallel_algorithms:
            for algo in self._parallel_algorithms:
                if algo not in self.ALGORITHM_HIERARCHY:
                    raise HashingError(f"Unsupported parallel algorithm: {algo}")
                parallel_settings = HashingSettings(algorithm=algo)
                self._parallel_hash_funcs[algo] = self._create_hash_function_for_settings(parallel_settings)

    def _create_hash_function_for_settings(self, settings: HashingSettings) -> Union[Any, Callable[[bytes], str]]:
        """Create a hash function for the given settings."""
        if settings.algorithm == "custom":
            if not settings.custom_module or not settings.custom_function:
                raise HashingError("Custom module and function must be specified")

            try:
                # Add security checks for custom module
                if not self._is_safe_module_path(settings.custom_module):
                    raise HashingError("Custom module path is not allowed")
                    
                module = importlib.import_module(settings.custom_module)
                return getattr(module, settings.custom_function)
            except (ImportError, AttributeError) as e:
                raise HashingError(f"Failed to load custom hash function: {str(e)}")

        if settings.algorithm in hashlib.algorithms_available:
            def hash_func(content: bytes) -> str:
                hasher = hashlib.new(settings.algorithm)
                hasher.update(content)
                return hasher.hexdigest()
            return hash_func

        raise HashingError(f"Unsupported hashing algorithm: {settings.algorithm}")

    def _create_hash_function(self) -> Union[Any, Callable[[bytes], str]]:
        """Get the appropriate hash function based on configuration."""
        return self._create_hash_function_for_settings(self.settings)

    def _is_safe_module_path(self, module_path: str) -> bool:
        """Check if a module path is safe to import.
        
        Implements basic security checks to prevent importing malicious modules.
        """
        # Disallow absolute paths and parent directory references
        if '/' in module_path or '\\' in module_path or '..' in module_path:
            return False
            
        # Only allow modules from specific trusted directories
        allowed_prefixes = ['mcard.', 'hashlib.', 'cryptography.']
        return any(module_path.startswith(prefix) for prefix in allowed_prefixes)

    async def hash_content(self, content: bytes) -> str:
        """Hash the given content using the configured algorithm."""
        if not isinstance(content, bytes):
            raise HashingError("Content must be bytes")

        try:
            # Get primary hash
            primary_hash = self._hash_func(content)
            
            # If parallel hashing is enabled, compute all hashes
            if self._parallel_algorithms:
                parallel_hashes = {}
                for algo, hash_func in self._parallel_hash_funcs.items():
                    try:
                        parallel_hashes[algo] = hash_func(content)
                    except Exception as e:
                        logger.warning(f"Parallel hashing failed for algorithm {algo}: {str(e)}")
                        
                # Store parallel hashes for later verification
                if hasattr(self, 'store') and self.store:
                    await self.store.save_parallel_hashes(primary_hash, parallel_hashes)
            
            return primary_hash
        except Exception as e:
            raise HashingError(f"Failed to hash content: {str(e)}")

    async def validate_hash(self, hash_str: str) -> bool:
        """
        Validate a hash string.
        
        Args:
            hash_str: Hash string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not hash_str:
            return False

        if not isinstance(hash_str, str):
            return False

        if self._hash_length and len(hash_str) != self._hash_length:
            return False

        try:
            # Check if the hash string contains only valid hex characters
            int(hash_str, 16)
            return True
        except ValueError:
            return False

    def validate_content(self, content: Any) -> bool:
        """
        Validate the content for hashing.
        
        Args:
            content: Content to validate
            
        Returns:
            True if valid, False otherwise
        """
        if content is None:
            return False

        # If content is bytes, it's valid
        if isinstance(content, bytes):
            return True

        # If content is string, it should be convertible to bytes
        if isinstance(content, str):
            try:
                content.encode('utf-8')
                return True
            except UnicodeEncodeError:
                return False

        # For any other type, try to convert to string first
        try:
            str(content).encode('utf-8')
            return True
        except (UnicodeEncodeError, TypeError):
            return False

    async def next_level_hash(self) -> Optional['DefaultHashingService']:
        """Get the next level hashing service with a stronger algorithm.
        
        Returns:
            A new DefaultHashingService instance with the next stronger algorithm,
            or None if no stronger algorithm is available.
        """
        current_strength = self.ALGORITHM_HIERARCHY.get(self.settings.algorithm.lower(), 0)
        logger.info(f"Current algorithm: {self.settings.algorithm} (strength: {current_strength})")
        
        # Find next strongest algorithm
        next_algo = None
        next_strength = current_strength
        
        for algo, strength in self.ALGORITHM_HIERARCHY.items():
            if strength > current_strength and (next_algo is None or strength < next_strength):
                next_algo = algo
                next_strength = strength
                
        if next_algo is None:
            logger.warning("No stronger hash algorithm available")
            return None
            
        logger.info(f"Transitioning to stronger algorithm: {next_algo} (strength: {next_strength})")
            
        # Create settings for next level
        new_settings = HashingSettings(
            algorithm=next_algo,
            custom_module=self.settings.custom_module if next_algo == 'custom' else None,
            custom_function=self.settings.custom_function if next_algo == 'custom' else None,
            custom_hash_length=self.settings.custom_hash_length if next_algo == 'custom' else None,
            parallel_algorithms=self.settings.parallel_algorithms
        )
        
        return DefaultHashingService(new_settings)

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
    if _default_service is None:
        if settings is None:
            settings = HashingSettings(algorithm="md5")
        _default_service = DefaultHashingService(settings)
    return _default_service

def set_hashing_service(service: Optional[DefaultHashingService]) -> None:
    """
    Set the global hashing service instance.
    
    Args:
        service: Hashing service to set as global default
    """
    global _default_service
    _default_service = service
