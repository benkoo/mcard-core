# Configuration Constants
# This file centralizes the management of static strings and constants used throughout the MCard project.
# It enhances maintainability by reducing duplication and ensuring consistency across various modules.

# Database Paths
# Used for specifying default and test database locations.
DEFAULT_DB_PATH = './data/DEFAULT_DB_FILE.db'
TEST_DB_PATH = './tests/data/test_mcard.db'

# Default Configuration Values
# These values are used as fallbacks when environment variables are not set.
DEFAULT_POOL_SIZE = 10  # Maximum number of database connections
DEFAULT_TIMEOUT = 30.0  # Timeout duration in seconds
DEFAULT_HASH_ALGORITHM = 'sha256'  # Default algorithm for hashing operations
DEFAULT_API_PORT = 5320
DEFAULT_API_KEY = 'your_api_key_here'  # Default API key for the application
DEFAULT_HASH_CUSTOM_MODULE = "custom_module"  # Module for custom hash functions
DEFAULT_HASH_CUSTOM_FUNCTION = "custom_function"  # Function name for custom hashing
DEFAULT_HASH_CUSTOM_LENGTH = 64  # Length of custom hash output

# Environment Variable Names
# These constants represent the names of environment variables used for configuration.
# They are used to fetch configuration values from the environment, providing flexibility and security.

# Hashing Configuration
# Constants related to hashing operations, allowing for customization and flexibility.
# These constants are used to define hashing algorithms and custom hashing functions.
ENV_HASH_ALGORITHM = "MCARD_HASH_ALGORITHM"

# Other Environment Variables
# General configuration constants for various application settings.
ENV_DB_PATH = "MCARD_DB_PATH"
ENV_DB_MAX_CONNECTIONS = "MCARD_STORE_MAX_CONNECTIONS"
ENV_DB_TIMEOUT = "MCARD_STORE_TIMEOUT"
ENV_SERVICE_LOG_LEVEL = "MCARD_SERVICE_LOG_LEVEL"
ENV_API_PORT = "MCARD_API_PORT"
ENV_FORCE_DEFAULT_CONFIG = "MCARD_FORCE_DEFAULT_CONFIG"
ENV_SERVER_HOST = "MCARD_SERVER_HOST"
ENV_API_KEY = "MCARD_API_KEY"

ENV_HASH_CUSTOM_MODULE = "MCARD_HASH_CUSTOM_MODULE"  # Module for custom hash functions
ENV_HASH_CUSTOM_FUNCTION = "MCARD_HASH_CUSTOM_FUNCTION"  # Function name for custom hashing
ENV_HASH_CUSTOM_LENGTH = "MCARD_HASH_CUSTOM_LENGTH"  # Length of custom hash output

API_KEY_HEADER_NAME = "X-API-Key"  # Header name for API key authentication

# Server Configuration Constants
SERVER_HOST = "0.0.0.0"
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 1000
MIN_PAGE_SIZE = 1

# Search Parameters
SEARCH_CONTENT_DEFAULT = True
SEARCH_HASH_DEFAULT = True
SEARCH_TIME_DEFAULT = True

# HTTP Status Codes
HTTP_STATUS_OK = 200  # Successful HTTP response status code
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

# Error messages
ERROR_INVALID_API_KEY = "Invalid API key"
ERROR_CARD_NOT_FOUND = "Card not found"
ERROR_CARD_CREATION_FAILED = "Failed to create card"
ERROR_CARD_DELETION_FAILED = "Failed to delete card"
ERROR_SERVER_SHUTDOWN = "Server shutdown failed"
ERROR_INVALID_CONTENT = "Content cannot be empty"
ERROR_INVALID_METADATA = "Metadata must be a dictionary"
ERROR_LISTING_CARDS = "Error listing cards"
ERROR_DELETE_ALL_CARDS_FAILED = "Failed to delete all cards"
SUCCESS_DELETE_ALL_CARDS = "All cards deleted successfully"
HEALTH_CHECK_SUCCESS = "Server is healthy"
HEALTH_CHECK_FAILURE = "Server health check failed"
ERROR_INVALID_CREDENTIALS = "Invalid credentials"
ERROR_CARD_ALREADY_EXISTS = "Card already exists"
ERROR_CARD_NOT_AUTHORIZED = "Card not authorized"
ERROR_INVALID_REQUEST = "Invalid request"
ERROR_INVALID_CARD_ID = "Invalid card ID"
ERROR_CARD_UPDATE_FAILED = "Failed to update card"
ERROR_CARD_NOT_UPDATED = "Card not updated"

# CORS origins
CORS_ORIGINS = [
    "http://localhost:3000",  # Default React dev server
    "http://localhost:8000",  # Default FastAPI dev server
    "https://localhost:3000",
    "https://localhost:8000",
    "http://localhost:8080",  # Additional CORS origin
    "https://example.com"  # Additional CORS origin
]
