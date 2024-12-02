# Configuration Constants
# This file centralizes the management of static strings and constants used throughout the MCard project.
# It enhances maintainability by reducing duplication and ensuring consistency across various modules.

# Database Paths
# Used for specifying default and test database locations.
DEFAULT_DB_PATH = './data/mcard.db'
TEST_DB_PATH = './tests/data/test_mcard.db'

# Default Configuration Values
# These values are used as fallbacks when environment variables are not set.
DEFAULT_POOL_SIZE = 10  # Maximum number of database connections
DEFAULT_TIMEOUT = 30.0  # Timeout duration in seconds
DEFAULT_HASH_ALGORITHM = 'sha256'  # Default algorithm for hashing operations
DEFAULT_API_PORT = 5320
DEFAULT_HASH_CUSTOM_MODULE = "custom_module"  # Module for custom hash functions
DEFAULT_HASH_CUSTOM_FUNCTION = "custom_function"  # Function name for custom hashing
DEFAULT_HASH_CUSTOM_LENGTH = "64"  # Length of custom hash output



# Environment Variable Names
# These constants represent the names of environment variables used for configuration.
# They are used to fetch configuration values from the environment, providing flexibility and security.

# Hashing Configuration
# Constants related to hashing operations, allowing for customization and flexibility.
# These constants are used to define hashing algorithms and custom hashing functions.
ENV_HASH_ALGORITHM = "MCARD_HASH_ALGORITHM"


# Other Environment Variables
# General configuration constants for various application settings.
ENV_DB_PATH = "MCARD_STORE_PATH"
ENV_DB_MAX_CONNECTIONS = "MCARD_STORE_MAX_CONNECTIONS"
ENV_DB_TIMEOUT = "MCARD_STORE_TIMEOUT"
ENV_SERVICE_LOG_LEVEL = "MCARD_SERVICE_LOG_LEVEL"
ENV_API_PORT = "MCARD_API_PORT"
ENV_FORCE_DEFAULT_CONFIG = "MCARD_FORCE_DEFAULT_CONFIG"

ENV_HASH_CUSTOM_MODULE = "MCARD_HASH_CUSTOM_MODULE"  # Module for custom hash functions
ENV_HASH_CUSTOM_FUNCTION = "MCARD_HASH_CUSTOM_FUNCTION"  # Function name for custom hashing
ENV_HASH_CUSTOM_LENGTH = "MCARD_HASH_CUSTOM_LENGTH"  # Length of custom hash output

