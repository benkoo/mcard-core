# MCard Core Configuration Guide

This guide provides detailed examples and explanations for configuring MCard Core.

## Configuration Constants

The `mcard/config_constants.py` file defines all configuration options available in MCard Core:

### Database Configuration
- `DEFAULT_DB_PATH`: Location of the SQLite database
- `DEFAULT_POOL_SIZE`: Maximum number of database connections
- `DEFAULT_TIMEOUT`: Database operation timeout in seconds

### Hashing Configuration
- `DEFAULT_HASH_ALGORITHM`: Default hashing algorithm (sha256)
- `DEFAULT_HASH_CUSTOM_MODULE`: Module path for custom hash functions
- `DEFAULT_HASH_CUSTOM_FUNCTION`: Function name for custom hashing
- `DEFAULT_HASH_CUSTOM_LENGTH`: Output length for custom hash functions

### API Configuration
- `DEFAULT_API_PORT`: Default port for the API server

## Environment Variables

All configuration can be customized through environment variables. The `.env.example` file shows the available options:

### Database Settings
```bash
# Database location and connection settings
MCARD_STORE_PATH=./data/mcard.db
MCARD_STORE_MAX_CONNECTIONS=10
MCARD_STORE_TIMEOUT=30.0
```

### Hashing Settings
```bash
# Choose from: md5, sha1, sha256, sha512
MCARD_HASH_ALGORITHM=sha256

# Custom hashing configuration
MCARD_HASH_CUSTOM_MODULE=myapp.hashing
MCARD_HASH_CUSTOM_FUNCTION=custom_hash
MCARD_HASH_CUSTOM_LENGTH=64
```

### API Settings
```bash
MCARD_API_PORT=5320
MCARD_SERVICE_LOG_LEVEL=INFO
```

## Configuration Precedence

1. Environment variables take highest precedence
2. Values in `.env` file override defaults
3. Default values from `config_constants.py` are used as fallback

## Testing Configuration

For testing, create a `.env.test` file with test-specific settings:
```bash
MCARD_STORE_PATH=./tests/data/test_mcard.db
MCARD_STORE_MAX_CONNECTIONS=5
MCARD_HASH_ALGORITHM=md5
```
