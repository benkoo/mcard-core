// Constants derived from server.py

// Server Configuration Constants
module.exports = {
    // Server Configuration
    SERVER_HOST: '0.0.0.0',
    DEFAULT_HOST: 'http://localhost',
    DEFAULT_PORT: 5320,
    DEFAULT_TIMEOUT: 5000,

    // Pagination Constants
    DEFAULT_PAGE: 1,
    DEFAULT_PAGE_SIZE: 10,
    MAX_PAGE_SIZE: 1000,
    MIN_PAGE_SIZE: 1,

    // Search Configuration
    SEARCH_CONTENT_DEFAULT: true,
    SEARCH_HASH_DEFAULT: true,
    SEARCH_TIME_DEFAULT: true,

    // API Key and Security
    API_KEY_HEADER_NAME: 'X-API-Key',
    DEFAULT_API_KEY: process.env.MCARD_API_KEY || 'dev_key_123',

    // HTTP Status Codes
    HTTP_STATUS_FORBIDDEN: 403,
    HTTP_STATUS_NOT_FOUND: 404,
    HTTP_STATUS_INTERNAL_SERVER_ERROR: 500,

    // Error Messages
    ERROR_INVALID_API_KEY: 'Invalid API key',
    ERROR_CARD_NOT_FOUND: 'Card not found',
    ERROR_CARD_CREATION_FAILED: 'Failed to create card',
    ERROR_CARD_DELETION_FAILED: 'Failed to delete card',
    ERROR_INVALID_CONTENT: 'Content cannot be empty',
    ERROR_INVALID_METADATA: 'Metadata must be a dictionary',
    ERROR_LISTING_CARDS: 'Error listing cards',
    ERROR_DELETE_ALL_CARDS_FAILED: 'Failed to delete all cards',

    // Logging Levels
    LOG_LEVELS: {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3
    },

    // Content Validation
    MAX_CONTENT_LENGTH: 100000000,
    MAX_QUERY_LENGTH: 500,

    // CORS Origins
    CORS_ORIGINS: [
        'http://localhost:3000',
        'http://localhost:8000',
        'https://localhost:3000',
        'https://localhost:8000'
    ]
};
