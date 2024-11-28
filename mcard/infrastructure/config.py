"""Configuration module for mcard."""
import os
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Type
from threading import Lock
from dotenv import load_dotenv
from mcard.infrastructure.persistence.engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.domain.dependency.hashing import HashingSettings

# Load environment variables from .env file
load_dotenv()

# Environment variable names
ENV_DB_PATH = "MCARD_STORE_DB_PATH"
ENV_DB_MAX_CONNECTIONS = "MCARD_STORE_MAX_CONNECTIONS"
ENV_DB_TIMEOUT = "MCARD_STORE_TIMEOUT"
ENV_HASH_ALGORITHM = "MCARD_HASH_ALGORITHM"
ENV_HASH_CUSTOM_MODULE = "MCARD_HASH_CUSTOM_MODULE"
ENV_HASH_CUSTOM_FUNCTION = "MCARD_HASH_CUSTOM_FUNCTION"
ENV_HASH_CUSTOM_LENGTH = "MCARD_HASH_CUSTOM_LENGTH"
ENV_FORCE_DEFAULT_CONFIG = "MCARD_FORCE_DEFAULT_CONFIG"

class ConfigurationSource(ABC):
    """Abstract base class for configuration sources."""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load configuration from the source."""
        pass

class EnvironmentConfigSource(ConfigurationSource):
    """Configuration source that loads from environment variables."""
    
    VALID_HASH_ALGORITHMS = {"md5", "sha1", "sha224", "sha256", "sha384", "sha512", "custom"}
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        # Get configuration from environment
        config = {
            'db_path': os.getenv(ENV_DB_PATH),
            'max_connections': os.getenv(ENV_DB_MAX_CONNECTIONS),
            'timeout': os.getenv(ENV_DB_TIMEOUT),
            'hash_algorithm': os.getenv(ENV_HASH_ALGORITHM),
            'hash_custom_module': os.getenv(ENV_HASH_CUSTOM_MODULE),
            'hash_custom_function': os.getenv(ENV_HASH_CUSTOM_FUNCTION),
            'hash_custom_length': os.getenv(ENV_HASH_CUSTOM_LENGTH),
        }
        
        # Validate and normalize configuration
        return self._validate_config(config)
        
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize configuration values."""
        validated = {}
        
        # Validate db_path
        db_path = config.get('db_path')
        if not db_path or not str(db_path).strip():
            validated['db_path'] = str(get_default_db_path())
        else:
            # Keep relative paths as-is
            db_path = str(db_path).strip()
            validated['db_path'] = db_path
        
        # Validate max_connections
        max_conn = config.get('max_connections')
        if max_conn is None:
            validated['max_connections'] = 5  # Default value
        else:
            max_conn_str = str(max_conn)
            if not max_conn_str or not max_conn_str.strip():
                raise ValueError("Maximum connections cannot be empty")
            try:
                max_conn_int = int(max_conn_str)
                if max_conn_int <= 0:
                    raise ValueError(f"Maximum connections must be positive, got {max_conn}")
                validated['max_connections'] = max_conn_int
            except ValueError as e:
                if "invalid literal for int()" in str(e):
                    raise ValueError(f"Invalid max_connections value: {max_conn}")
                raise

        # Validate timeout
        timeout = config.get('timeout')
        if timeout is None:
            validated['timeout'] = 30.0  # Default value
        else:
            timeout_str = str(timeout)
            if not timeout_str or not timeout_str.strip():
                raise ValueError("Timeout cannot be empty")
            try:
                timeout_float = float(timeout_str)
                if timeout_float <= 0:
                    raise ValueError(f"Timeout must be positive, got {timeout}")
                validated['timeout'] = timeout_float
            except ValueError as e:
                if "could not convert string to float" in str(e):
                    raise ValueError(f"Invalid timeout value: {timeout}")
                raise

        # Validate hash algorithm
        hash_algo = config.get('hash_algorithm')
        if hash_algo is None or not str(hash_algo).strip():
            validated['hash_algorithm'] = "sha256"  # Default value
            validated['hash_custom_module'] = None
            validated['hash_custom_function'] = None
            validated['hash_custom_length'] = None
        else:
            hash_algo = str(hash_algo).strip().lower()
            if hash_algo not in self.VALID_HASH_ALGORITHMS:
                raise ValueError(f"Invalid hash algorithm: {hash_algo}")
            validated['hash_algorithm'] = hash_algo

            # Get custom hash settings
            custom_module = config.get('hash_custom_module')
            custom_function = config.get('hash_custom_function')
            hash_length = config.get('hash_custom_length')

            # Validate custom hash settings
            if hash_algo == "custom":
                if not custom_module or not str(custom_module).strip():
                    raise ValueError("Custom hash module must be specified when using custom algorithm")
                if not custom_function or not str(custom_function).strip():
                    raise ValueError("Custom hash function must be specified when using custom algorithm")
                validated['hash_custom_module'] = str(custom_module).strip()
                validated['hash_custom_function'] = str(custom_function).strip()
            else:
                # For non-custom algorithms, preserve custom settings if provided
                if custom_module and str(custom_module).strip():
                    validated['hash_custom_module'] = str(custom_module).strip()
                else:
                    validated['hash_custom_module'] = None
                    
                if custom_function and str(custom_function).strip():
                    validated['hash_custom_function'] = str(custom_function).strip()
                else:
                    validated['hash_custom_function'] = None

            # Validate hash length if provided
            if hash_length is not None:
                hash_length_str = str(hash_length)
                if not hash_length_str or not hash_length_str.strip():
                    raise ValueError("Hash length cannot be empty")
                try:
                    length = int(hash_length_str)
                    if length <= 0:
                        raise ValueError(f"Hash length must be positive, got {length}")
                    validated['hash_custom_length'] = length
                except ValueError as e:
                    if "invalid literal for int()" in str(e):
                        raise ValueError(f"Invalid hash length value: {hash_length}")
                    raise
            else:
                validated['hash_custom_length'] = None

        return validated

class TestConfigSource(ConfigurationSource):
    """Configuration source for test environment."""
    
    def load(self) -> Dict[str, Any]:
        """Load test configuration."""
        # Start with test defaults
        config = {
            'db_path': "data/test_mcard.db",  # Use test-specific path by default
            'max_connections': 5,  # Default test connections
            'timeout': 30.0,  # Default test timeout
            'hash_algorithm': "sha256",  # Default test hash algorithm
            'hash_custom_module': None,  # No custom hash by default
            'hash_custom_function': None,
            'hash_custom_length': None,
        }
        
        # Allow environment variables to override test defaults
        env_overrides = {
            'db_path': os.getenv(ENV_DB_PATH),
            'max_connections': os.getenv(ENV_DB_MAX_CONNECTIONS),
            'timeout': os.getenv(ENV_DB_TIMEOUT),
            'hash_algorithm': os.getenv(ENV_HASH_ALGORITHM),
            'hash_custom_module': os.getenv(ENV_HASH_CUSTOM_MODULE),
            'hash_custom_function': os.getenv(ENV_HASH_CUSTOM_FUNCTION),
            'hash_custom_length': os.getenv(ENV_HASH_CUSTOM_LENGTH),
        }
        
        # Update config with non-None environment values
        for key, value in env_overrides.items():
            if value is not None:
                config[key] = value
        
        # Validate and return the configuration
        return self._validate_config(config)

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize configuration values."""
        validated = {}
        
        # Validate db_path
        db_path = config.get('db_path')
        if not db_path or not str(db_path).strip():
            validated['db_path'] = str(get_test_db_path())  # Use test-specific path as fallback
        else:
            # Keep relative paths as-is
            db_path = str(db_path).strip()
            validated['db_path'] = db_path
        
        # Validate max_connections
        max_conn = config.get('max_connections')
        if max_conn is None:
            validated['max_connections'] = 5  # Default value
        else:
            max_conn_str = str(max_conn)
            if not max_conn_str or not max_conn_str.strip():
                raise ValueError("Maximum connections cannot be empty")
            try:
                max_conn_int = int(max_conn_str)
                if max_conn_int <= 0:
                    raise ValueError(f"Maximum connections must be positive, got {max_conn}")
                validated['max_connections'] = max_conn_int
            except ValueError as e:
                if "invalid literal for int()" in str(e):
                    raise ValueError(f"Invalid max_connections value: {max_conn}")
                raise

        # Validate timeout
        timeout = config.get('timeout')
        if timeout is None:
            validated['timeout'] = 30.0  # Default value
        else:
            timeout_str = str(timeout)
            if not timeout_str or not timeout_str.strip():
                raise ValueError("Timeout cannot be empty")
            try:
                timeout_float = float(timeout_str)
                if timeout_float <= 0:
                    raise ValueError(f"Timeout must be positive, got {timeout}")
                validated['timeout'] = timeout_float
            except ValueError as e:
                if "could not convert string to float" in str(e):
                    raise ValueError(f"Invalid timeout value: {timeout}")
                raise

        # Validate hash algorithm
        hash_algo = config.get('hash_algorithm')
        if hash_algo is None or not str(hash_algo).strip():
            validated['hash_algorithm'] = "sha256"  # Default value
            validated['hash_custom_module'] = None
            validated['hash_custom_function'] = None
            validated['hash_custom_length'] = None
        else:
            hash_algo = str(hash_algo).strip().lower()
            if hash_algo not in EnvironmentConfigSource.VALID_HASH_ALGORITHMS:
                raise ValueError(f"Invalid hash algorithm: {hash_algo}")
            validated['hash_algorithm'] = hash_algo

            # Get custom hash settings
            custom_module = config.get('hash_custom_module')
            custom_function = config.get('hash_custom_function')
            hash_length = config.get('hash_custom_length')

            # Validate custom hash settings
            if hash_algo == "custom":
                if not custom_module or not str(custom_module).strip():
                    raise ValueError("Custom hash module must be specified when using custom algorithm")
                if not custom_function or not str(custom_function).strip():
                    raise ValueError("Custom hash function must be specified when using custom algorithm")
                validated['hash_custom_module'] = str(custom_module).strip()
                validated['hash_custom_function'] = str(custom_function).strip()
            else:
                # For non-custom algorithms, preserve custom settings if provided
                if custom_module and str(custom_module).strip():
                    validated['hash_custom_module'] = str(custom_module).strip()
                else:
                    validated['hash_custom_module'] = None
                    
                if custom_function and str(custom_function).strip():
                    validated['hash_custom_function'] = str(custom_function).strip()
                else:
                    validated['hash_custom_function'] = None

            # Validate hash length if provided
            if hash_length is not None:
                hash_length_str = str(hash_length)
                if not hash_length_str or not hash_length_str.strip():
                    raise ValueError("Hash length cannot be empty")
                try:
                    length = int(hash_length_str)
                    if length <= 0:
                        raise ValueError(f"Hash length must be positive, got {length}")
                    validated['hash_custom_length'] = length
                except ValueError as e:
                    if "invalid literal for int()" in str(e):
                        raise ValueError(f"Invalid hash length value: {hash_length}")
                    raise
            else:
                validated['hash_custom_length'] = None

        return validated

class DataEngineConfig:
    """Configuration for the data engine."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize configuration."""
        if not hasattr(self, '_initialized'):
            self.repository = None
            self.hashing = None
            self._initialized = False
    
    @classmethod
    def get_instance(cls) -> 'DataEngineConfig':
        """Get singleton instance."""
        return cls()
    
    @classmethod
    def reset(cls):
        """Reset singleton instance for testing."""
        cls._instance = None
    
    def configure(self, source: ConfigurationSource):
        """Configure using provided source."""
        if self._initialized:
            raise RuntimeError("Configuration is already initialized")
        
        config = source.load()
        
        # Configure repository
        self.repository = SQLiteConfig(
            db_path=config['db_path'],
            max_connections=config['max_connections'],
            timeout=config['timeout'],
            check_same_thread=False
        )
        
        # Configure hashing
        self.hashing = HashingSettings(
            algorithm=config['hash_algorithm'],
            custom_module=config.get('hash_custom_module'),
            custom_function=config.get('hash_custom_function'),
            custom_hash_length=config.get('hash_custom_length')
        )
        
        self._initialized = True

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_default_db_path() -> Path:
    """Get the default database path."""
    return Path("data/mcard.db")

def get_test_db_path() -> Path:
    """Get the test database path."""
    return Path("data/test_mcard.db")

def load_config() -> DataEngineConfig:
    """
    Load configuration based on the environment.
    
    Returns:
        DataEngineConfig: The configured singleton instance
    """
    config = DataEngineConfig.get_instance()
    
    # Check if we should force default config
    force_default = os.getenv(ENV_FORCE_DEFAULT_CONFIG, "").lower() == "true"
    
    # Check if we're in test mode
    in_test_mode = not force_default and "PYTEST_CURRENT_TEST" in os.environ
    
    # Reset for tests to ensure clean state
    if in_test_mode:
        DataEngineConfig.reset()
        config = DataEngineConfig.get_instance()
        source = TestConfigSource()
    # Return existing config if already initialized and not in test mode
    elif config._initialized:
        return config
    # Load from environment for first-time initialization
    else:
        source = EnvironmentConfigSource()
    
    # Configure and return
    config.configure(source)
    return config
