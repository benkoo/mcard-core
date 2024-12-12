"""Configuration module for mcard."""
import os
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Type, Union, Protocol
from threading import Lock
from dotenv import load_dotenv
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig, EngineConfig, EngineType
from mcard.domain.services.hashing import HashingSettings
from mcard.config_constants import DEFAULT_DB_PATH, TEST_DB_PATH, DEFAULT_POOL_SIZE, DEFAULT_TIMEOUT, DEFAULT_HASH_ALGORITHM, ENV_DB_PATH, ENV_DB_MAX_CONNECTIONS, ENV_DB_TIMEOUT, ENV_HASH_ALGORITHM, ENV_HASH_CUSTOM_MODULE, ENV_HASH_CUSTOM_FUNCTION, ENV_HASH_CUSTOM_LENGTH, ENV_FORCE_DEFAULT_CONFIG

# Load environment variables from .env file
load_dotenv()

class ConfigurationSource(Protocol):
    """Protocol for configuration sources."""
    
    def load(self) -> Dict[str, Any]:
        """Load configuration."""
        ...

    def configure_repository(self) -> SQLiteConfig:
        """Configure repository."""
        ...

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
        """
        Validate and normalize configuration values.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            Validated configuration dictionary
        """
        validated = {}
        
        # Validate db_path
        db_path = config.get('db_path')
        validated['db_path'] = resolve_db_path(db_path)
        
        # Validate max_connections
        max_conn = config.get('max_connections')
        validated['max_connections'] = int(max_conn) if max_conn is not None else DEFAULT_POOL_SIZE
        
        # Validate timeout
        timeout = config.get('timeout')
        validated['timeout'] = float(timeout) if timeout is not None else DEFAULT_TIMEOUT
        
        # Validate hash algorithm
        hash_algo = config.get('hash_algorithm')
        if hash_algo is None or not str(hash_algo).strip():
            validated['hash_algorithm'] = DEFAULT_HASH_ALGORITHM  # Default value
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

    def configure_repository(self) -> SQLiteConfig:
        """Configure SQLite repository from environment."""
        config = self.load()
        return SQLiteConfig(
            db_path=config['db_path'],
            max_connections=config['max_connections'],
            timeout=config['timeout']
        )

class TestConfigSource(ConfigurationSource):
    """Configuration source for test environment."""
    
    def load(self) -> Dict[str, Any]:
        """Load test configuration."""
        # Start with test defaults
        config = {
            'db_path': TEST_DB_PATH,  # Use test-specific path by default
            'max_connections': 5,  # Default test connections
            'timeout': 30.0,  # Default test timeout
            'hash_algorithm': DEFAULT_HASH_ALGORITHM,  # Default test hash algorithm
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
        return self._validate_config(config, is_test=True)

    def _validate_config(self, config: Dict[str, Any], is_test: bool = False) -> Dict[str, Any]:
        """
        Validate and normalize configuration values.
        
        Args:
            config: Configuration dictionary
            is_test: Whether this is a test configuration
        
        Returns:
            Validated configuration dictionary
        """
        validated = {}
        
        # Validate db_path with test flag
        db_path = config.get('db_path')
        validated['db_path'] = resolve_db_path(db_path, is_test)
        
        # Validate max_connections
        max_conn = config.get('max_connections')
        validated['max_connections'] = int(max_conn) if max_conn is not None else DEFAULT_POOL_SIZE
        
        # Validate timeout
        timeout = config.get('timeout')
        validated['timeout'] = float(timeout) if timeout is not None else DEFAULT_TIMEOUT
        
        # Validate hash algorithm
        hash_algo = config.get('hash_algorithm')
        if hash_algo is None or not str(hash_algo).strip():
            validated['hash_algorithm'] = DEFAULT_HASH_ALGORITHM  # Default value
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

    def configure_repository(self) -> SQLiteConfig:
        """Configure test SQLite repository."""
        config = self.load()
        return SQLiteConfig(
            db_path=config['db_path'],
            max_connections=config['max_connections'],
            timeout=config['timeout']
        )

class DataEngineConfig:
    """Configuration management for data engine."""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton implementation."""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration."""
        if not hasattr(self, '_initialized'):
            self.repository = None
            self.engine_config = None
            self.pool_size = DEFAULT_POOL_SIZE  # Default pool size
            self.timeout = DEFAULT_TIMEOUT  # Default timeout
            self.engine_options = {'check_same_thread': False}
            self.max_content_size = 5 * 1024 * 1024  # Default 5MB
            
            # Add hashing configuration
            self.hashing = {
                'algorithm': DEFAULT_HASH_ALGORITHM
            }
            
            self._initialized = True

    @property
    def max_content_size(self):
        """Get max content size."""
        return self.engine_config.max_content_size if self.engine_config else None

    @max_content_size.setter
    def max_content_size(self, value):
        """Set max content size."""
        if self.engine_config:
            self.engine_config.max_content_size = value

    @classmethod
    def reset(cls):
        """Reset the singleton instance and class-level attributes."""
        with cls._lock:
            cls._instance = None
            # Reinitialize class-level attributes
            if hasattr(cls, '_initialized'):
                delattr(cls, '_initialized')

    def configure(self, source: ConfigurationSource):
        """
        Configure the data engine with a specific source.
        
        Args:
            source: Configuration source
        """
        # Reset existing configuration
        self.reset()

        # Load configuration from source
        config = source.load()

        # Set repository configuration
        self.repository = source.configure_repository()
        
        # Set engine configuration
        self.engine_config = create_engine_config(
            engine_type=EngineType.SQLITE,
            connection_string=config['db_path'],
            max_connections=config.get('max_connections', DEFAULT_POOL_SIZE),
            timeout=config.get('timeout', DEFAULT_TIMEOUT)
        )

        # Update additional configuration
        self.pool_size = config.get('max_connections', DEFAULT_POOL_SIZE)
        self.timeout = config.get('timeout', DEFAULT_TIMEOUT)
        self.engine_options = {
            'check_same_thread': False,
            'max_content_size': 10 * 1024 * 1024  # 10 MB default
        }

        # Update hashing configuration
        self.hashing = config.get('hashing', {
            'algorithm': DEFAULT_HASH_ALGORITHM
        })

def create_engine_config(
    engine_type: EngineType,
    connection_string: str,
    max_connections: Optional[int] = None,
    timeout: Optional[float] = None
) -> SQLiteConfig:
    """
    Create an engine configuration based on parameters.
    
    Args:
        engine_type: Type of database engine
        connection_string: Database connection string
        max_connections: Maximum number of connections
        timeout: Connection timeout
    
    Returns:
        SQLite configuration
    """
    return SQLiteConfig(
        db_path=connection_string,
        max_connections=max_connections or DEFAULT_POOL_SIZE,
        timeout=timeout or DEFAULT_TIMEOUT
    )

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_default_db_path() -> str:
    """Get the default database path."""
    return DEFAULT_DB_PATH

def get_test_db_path() -> str:
    """Get the test database path."""
    return TEST_DB_PATH

def resolve_db_path(db_path: Union[str, Path], is_test: bool = False) -> str:
    """
    Resolve database path with flexible handling.
    
    Args:
        db_path: Input database path
        is_test: Whether this is a test configuration
    
    Returns:
        Resolved database path as a string
    """
    # If no path is provided, use default paths
    if not db_path or str(db_path).strip() == '':
        return get_test_db_path() if is_test else get_default_db_path()
    
    # Convert to Path
    path = Path(str(db_path).strip())
    
    # If absolute path, try to make it relative
    if path.is_absolute():
        try:
            return str(path.relative_to(get_project_root()))
        except ValueError:
            return str(path)
    
    return str(path)

def load_config(is_test_mode: bool = False) -> DataEngineConfig:
    """
    Load configuration for the data engine.
    
    Args:
        is_test_mode: Flag to indicate test mode
    
    Returns:
        Configured DataEngineConfig
    """
    config = DataEngineConfig()
    config.configure(EnvironmentConfigSource() if not is_test_mode else TestConfigSource())

    return config
