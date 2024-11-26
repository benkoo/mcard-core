"""Configuration module for MCard."""
import os
import importlib
from pathlib import Path
from typing import Optional, Callable, Any
from dotenv import load_dotenv


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parents[1]


def load_config(env_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = get_project_root() / ".env"
    load_dotenv(env_path)


def get_data_source() -> str:
    """Get the data source directory path."""
    data_source = os.getenv("MCARD_DATA_SOURCE")
    if not data_source:
        raise ValueError("MCARD_DATA_SOURCE not set in environment")
    return str(get_project_root() / data_source)


def get_db_path(test: bool = False) -> str:
    """Get the database path."""
    env_var = "MCARD_TEST_DB" if test else "MCARD_DB"
    db_path = os.getenv(env_var)
    if not db_path:
        raise ValueError(f"{env_var} not set in environment")
    
    # Convert to absolute path and ensure directory exists
    db_path = get_project_root() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


def get_hash_config() -> tuple[str, Optional[tuple[Callable[[bytes], str], int]]]:
    """
    Get hash function configuration from environment.
    
    Returns:
        tuple: (hash_function_name, Optional tuple of (custom_function, expected_length))
        
    Environment variables used:
        MCARD_HASH_FUNCTION: The hash function to use (sha256, sha512, sha1, md5, or custom)
        MCARD_CUSTOM_HASH_MODULE: For custom hash function, the module path (e.g., "mypackage.hashing")
        MCARD_CUSTOM_HASH_FUNCTION: For custom hash function, the function name in the module
        MCARD_CUSTOM_HASH_LENGTH: For custom hash function, the expected length of the hash
    """
    hash_function_str = os.getenv("MCARD_HASH_FUNCTION", "sha256").lower()
    valid_hash_functions = {"sha256", "sha512", "sha1", "md5", "custom"}
    
    if hash_function_str not in valid_hash_functions:
        raise ValueError(f"Invalid hash function '{hash_function_str}'. "
                        f"Must be one of: {', '.join(valid_hash_functions)}")
    
    if hash_function_str == "custom":
        module_path = os.getenv("MCARD_CUSTOM_HASH_MODULE")
        function_name = os.getenv("MCARD_CUSTOM_HASH_FUNCTION")
        hash_length_str = os.getenv("MCARD_CUSTOM_HASH_LENGTH")
        
        if not all([module_path, function_name, hash_length_str]):
            raise ValueError(
                "For custom hash function, all these environment variables must be set: "
                "MCARD_CUSTOM_HASH_MODULE, MCARD_CUSTOM_HASH_FUNCTION, MCARD_CUSTOM_HASH_LENGTH"
            )
        
        try:
            hash_length = int(hash_length_str)
        except ValueError:
            raise ValueError("MCARD_CUSTOM_HASH_LENGTH must be an integer")
        
        try:
            module = importlib.import_module(module_path)
            hash_function_impl = getattr(module, function_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Error loading custom hash function: {str(e)}")
        
        return hash_function_str, (hash_function_impl, hash_length)
    
    return hash_function_str, None


# Load configuration at module import time
load_config()

# Initialize hash configuration
from .core import HashingConfig, HashFunction

config = HashingConfig.get_instance()
hash_function_str, custom_config = get_hash_config()

if hash_function_str == "custom":
    if custom_config is None:
        raise ValueError("Custom hash configuration is missing")
    custom_func, expected_length = custom_config
    config.set_custom_hash_function(custom_func, expected_length)
else:
    config.hash_function = HashFunction(hash_function_str)
