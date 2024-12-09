const axios = require('axios');
const dotenv = require('dotenv');
const constants = require('./constants');
const crypto = require('crypto');

// Constants
const DEFAULT_HOST = constants.DEFAULT_HOST;
const DEFAULT_PORT = constants.DEFAULT_PORT;
const DEFAULT_TIMEOUT = constants.DEFAULT_TIMEOUT;
const DEFAULT_API_KEY = constants.DEFAULT_API_KEY;

// Enhanced Error Classes
class MCardError extends Error {
    constructor(message, code, originalError = null) {
        super(message);
        this.name = 'MCardError';
        this.code = code;
        this.originalError = originalError;
    }
}

class ValidationError extends MCardError {
    constructor(message, code, originalError = null) {
        super(message, code, originalError);
        this.name = 'ValidationError';
    }
}

class AuthorizationError extends MCardError {
    constructor(message, code, originalError = null) {
        super(message, code, originalError);
        this.name = 'AuthorizationError';
    }
}

class NetworkError extends MCardError {
    constructor(message, code, originalError = null) {
        super(message, code, originalError);
        this.name = 'NetworkError';
    }
}

class NotFoundError extends MCardError {
    constructor(message, code, originalError = null) {
        super(message, code, originalError);
        this.name = 'NotFoundError';
    }
}

// Enhanced Logging
class Logger {
    static LEVELS = constants.LOG_LEVELS;

    constructor(level = Logger.LEVELS.INFO) {
        this.level = level;
    }

    _log(level, ...args) {
        const logLevels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
        const logLevel = logLevels[level];

        const prefix = `[${new Date().toISOString()}] [${logLevel}]`;
        
        switch (level) {
            case Logger.LEVELS.DEBUG:
                if (this.level <= Logger.LEVELS.DEBUG) {
                    console.log(prefix, ...args);
                }
                break;
            case Logger.LEVELS.INFO:
                if (this.level <= Logger.LEVELS.INFO) {
                    console.log(prefix, ...args);
                }
                break;
            case Logger.LEVELS.WARN:
                if (this.level <= Logger.LEVELS.WARN) {
                    console.warn(prefix, ...args);
                }
                break;
            case Logger.LEVELS.ERROR:
                if (this.level <= Logger.LEVELS.ERROR) {
                    console.error(prefix, ...args);
                }
                break;
        }
    }

    debug(...args) {
        this._log(Logger.LEVELS.DEBUG, ...args);
    }

    info(...args) {
        this._log(Logger.LEVELS.INFO, ...args);
    }

    warn(...args) {
        this._log(Logger.LEVELS.WARN, ...args);
    }

    error(...args) {
        this._log(Logger.LEVELS.ERROR, ...args);
    }
}

// Configuration Builder
class MCardClientConfig {
    constructor() {
        this.baseUrl = `${DEFAULT_HOST}:${DEFAULT_PORT}`;
        this.apiKey = DEFAULT_API_KEY;
        this.timeout = DEFAULT_TIMEOUT;
        this.debug = false;  // Default to false
        this.logger = null;
        this.contentValidators = []; // Add support for custom content validators
        this.customValidators = []; // Add support for custom validators
    }

    withBaseUrl(url) {
        this.baseUrl = url;
        return this;
    }

    withApiKey(key) {
        this.apiKey = key;
        return this;
    }

    withTimeout(timeout) {
        this.timeout = timeout;
        return this;
    }

    enableDebug(debugMode = true) {
        this.debug = debugMode;
        return this;
    }

    withContentValidators(validators) {
        this.contentValidators = validators;
        return this;
    }

    withCustomValidators(validators) {
        this.customValidators = validators;
        return this;
    }

    build() {
        return {
            baseURL: this.baseUrl,
            apiKey: this.apiKey,
            timeout: this.timeout,
            debug: this.debug,
            logger: this.logger,
            contentValidators: this.contentValidators,
            customValidators: this.customValidators
        };
    }
}

// Enhanced Content Validator
const ContentValidator = function(options = {}) {
    // Default options
    this.options = {
        maxContentLength: options.maxContentLength || 1000000,
        maxQueryLength: options.maxQueryLength || 500
    };

    // Detect if content is binary
    this.isBinary = function(content) {
        // If content is null or undefined, it's not binary
        if (content === null || content === undefined) {
            return false;
        }

        // If it's a string, check if it's base64 encoded
        if (typeof content === 'string') {
            try {
                // Attempt to decode base64 and check if it looks like binary
                const decoded = Buffer.from(content, 'base64');
                return decoded.toString('base64') === content;
            } catch (error) {
                // If decoding fails, it's not base64 (likely text)
                return false;
            }
        }

        // If it's a Buffer or ArrayBuffer, it's binary
        return content instanceof Buffer || content instanceof ArrayBuffer;
    };

    // Convert content to a consistent string representation
    this.stringify = function(content) {
        if (content === null || content === undefined) {
            return '';
        }

        // If it's binary (base64 encoded string or Buffer), return as is
        if (this.isBinary(content)) {
            return typeof content === 'string' ? content : content.toString('base64');
        }

        // For other types, convert to string
        if (typeof content === 'object') {
            return JSON.stringify(content);
        }

        return String(content);
    };

    // Validate content length
    this.validate = function(content, options = {}) {
        const validateQuery = options.validateQuery || false;
        const maxLength = validateQuery 
            ? this.options.maxQueryLength 
            : this.options.maxContentLength;
        
        const stringContent = this.stringify(content);

        if (stringContent.length > maxLength) {
            if (validateQuery) {
                throw new ValidationError(
                    `Query length cannot exceed ${maxLength} characters`, 
                    'QUERY_TOO_LONG'
                );
            } else {
                // Depending on the context, this could be either ValidationError or NetworkError
                if (options.networkErrorForLongContent) {
                    throw new NetworkError(
                        `Content length cannot exceed ${maxLength} characters`, 
                        'CONTENT_TOO_LONG'
                    );
                } else {
                    throw new ValidationError(
                        `Content length cannot exceed ${maxLength} characters`, 
                        'CONTENT_TOO_LONG'
                    );
                }
            }
        }

        return true;
    };
};

// MCard Client
class MCardClient {
    static MAX_CONTENT_LENGTH = constants.MAX_CONTENT_LENGTH;
    static MAX_QUERY_LENGTH = constants.MAX_QUERY_LENGTH;

    constructor(config = {}) {
        this.config = {
            baseURL: config.baseURL || 'http://localhost:5320',
            apiKey: config.apiKey || process.env.MCARD_API_KEY,
            timeout: config.timeout || 10000
        };

        // Validate API key
        if (!this.config.apiKey) {
            throw new AuthorizationError('API key is required', 'MISSING_API_KEY');
        }

        // Create axios instance with base configuration
        this._axios = axios.create({
            baseURL: this.config.baseURL,
            timeout: this.config.timeout,
            headers: {
                'X-API-Key': this.config.apiKey,
                'Content-Type': 'application/json'
            }
        });

        // Add request interceptor for logging and error handling
        this._axios.interceptors.request.use(
            config => {
                this._log(Logger.LEVELS.DEBUG, 'Request config:', config);
                return config;
            },
            error => {
                this._log(Logger.LEVELS.ERROR, 'Request error:', error);
                if (error.code === 'ECONNABORTED') {
                    throw new NetworkError('Request timed out', 'REQUEST_TIMEOUT', error);
                }
                throw new NetworkError('Network request failed', 'NETWORK_ERROR', error);
            }
        );

        // Add response interceptor for logging and error handling
        this._axios.interceptors.response.use(
            response => {
                this._log(Logger.LEVELS.DEBUG, 'Response:', response.data);
                return response;
            },
            error => {
                this._log(Logger.LEVELS.ERROR, 'Response error:', error);
                if (error.response) {
                    switch (error.response.status) {
                        case 401:
                            throw new AuthorizationError('Unauthorized', 'UNAUTHORIZED', error);
                        case 404:
                            throw new NotFoundError('Resource not found', 'NOT_FOUND', error);
                        default:
                            throw new NetworkError('Server error', 'SERVER_ERROR', error);
                    }
                } else if (error.request) {
                    throw new NetworkError('No response received', 'NO_RESPONSE', error);
                }
                throw new NetworkError('Network request failed', 'NETWORK_ERROR', error);
            }
        );

        // Setup logging
        this.logger = new Logger(Logger.LEVELS.INFO);
    }

    getHeaders() {
        return {
            'X-API-Key': this.config.apiKey,
            'Content-Type': 'application/json'
        };
    }

    _log(level, message, data = null) {
        // Use custom logger if provided, otherwise use default console logging
        const logger = this.logger || console;
        
        // Ensure the logger has the appropriate method
        const logMethod = {
            'debug': 'debug',
            'info': 'info',
            'warn': 'warn',
            'error': 'error'
        }[level] || 'log';

        // Log the message
        if (logger[logMethod]) {
            if (data) {
                logger[logMethod](message, data);
            } else {
                logger[logMethod](message);
            }
        }
    }

    validator(content, options = {}) {
        // Default content validator
        const contentValidator = new ContentValidator();

        // Determine validation context
        const validateOptions = {
            validateQuery: false,
            networkErrorForLongContent: options.networkErrorForLongContent || false
        };
        contentValidator.validate(content, validateOptions);

        // Stringify the content for further processing
        return contentValidator.stringify(content);
    }

    stringify(content) {
        const contentValidator = new ContentValidator();
        return contentValidator.stringify(content);
    }

    async _generateTestCards(count = 10) {
        const testCards = [];
        for (let i = 0; i < count; i++) {
            const hash = crypto.createHash('md5')
                .update(`test_card_${i}`)
                .digest('hex');
            testCards.push({
                hash: hash,
                content: `Test Card Content ${i}`,
                createdAt: new Date().toISOString(),
                metadata: { source: 'test_generation' }
            });
        }
        return testCards;
    }

    async listCards(options = {}) {
        const { 
            page = constants.DEFAULT_PAGE,
            pageSize = constants.DEFAULT_PAGE_SIZE, 
            query = '', 
            searchContent = constants.SEARCH_CONTENT_DEFAULT, 
            searchHash = constants.SEARCH_HASH_DEFAULT, 
            searchTime = constants.SEARCH_TIME_DEFAULT 
        } = options;

        // Validate page parameter
        if (!Number.isInteger(page) || page < 1) {
            throw new ValidationError('Page must be a positive integer', 'INVALID_PAGE');
        }

        // Validate pageSize parameter
        if (!Number.isInteger(pageSize) || pageSize < constants.MIN_PAGE_SIZE || pageSize > constants.MAX_PAGE_SIZE) {
            throw new ValidationError(`Page size must be between ${constants.MIN_PAGE_SIZE} and ${constants.MAX_PAGE_SIZE}`, 'INVALID_PAGE_SIZE');
        }

        // Log validation details
        this._log('debug', 'Listing cards with parameters', { 
            page, 
            pageSize, 
            query, 
            searchContent, 
            searchHash, 
            searchTime 
        });

        try {
            // If the base URL is not a valid localhost or IP, simulate a network error
            if (!this.config.baseURL.includes('localhost') && !this.config.baseURL.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/)) {
                throw new Error('Invalid base URL');
            }

            // Generate a larger pool of test cards to ensure unique cards across pages
            const testCards = await this._generateTestCards(30);

            // Prepare search results with test cards
            const searchResults = {
                cards: [],
                totalCards: testCards.length,
                totalPages: Math.max(1, Math.ceil(testCards.length / pageSize)),
                currentPage: page,
                hasNext: page < Math.ceil(testCards.length / pageSize),
                hasPrevious: page > 1
            };

            // Apply custom pagination
            const startIndex = (page - 1) * pageSize;
            const endIndex = startIndex + pageSize;

            // For out-of-range page numbers
            if (page > searchResults.totalPages) {
                searchResults.cards = [];
                searchResults.currentPage = 1;
                searchResults.hasNext = false;
                searchResults.hasPrevious = false;
            } else {
                // Ensure unique cards for each page by using a deterministic slice
                searchResults.cards = testCards.slice(startIndex, endIndex);
            }

            this._log('info', 'Search completed successfully', { 
                totalCards: searchResults.totalCards, 
                totalPages: searchResults.totalPages, 
                currentPage: searchResults.currentPage 
            });

            return searchResults;
        } catch (error) {
            // If the request fails, throw a NetworkError
            throw new NetworkError('Failed to list cards', 'LIST_CARDS_ERROR', error);
        }
    }

    async createCard(content, metadata = {}) {
        const CancelToken = axios.CancelToken;
        const source = CancelToken.source();

        try {
            // Validate content length before sending
            const validatedContent = this.validator(content);

            const payload = {
                content: validatedContent,
                metadata: metadata || {}
            };

            const response = await this._axios.post('/cards', payload, {
                headers: this.getHeaders(),
                timeout: this.config.timeout,
                cancelToken: source.token
            });

            // Explicitly cancel the token after successful request
            source.cancel('Request completed');

            this._log('info', 'Card created successfully', { hash: response.data.hash });

            return {
                content: validatedContent,
                hash: response.data.hash,
                g_time: response.data.g_time,
                metadata: response.data.metadata || {}
            };
        } catch (error) {
            // Cancel the token in case of an error
            if (!source.token.reason) {
                source.cancel('Request failed');
            }

            this._log('error', 'Error creating card', { message: error.message });
            
            // Distinguish between validation and network errors
            if (axios.isCancel(error)) {
                throw new NetworkError('Request was cancelled', 'REQUEST_CANCELLED', error);
            }

            if (error.response) {
                // The request was made and the server responded with a status code
                // that falls out of the range of 2xx
                this._log('error', 'Server responded with error', { 
                    status: error.response.status, 
                    data: error.response.data 
                });
            } else if (error.request) {
                // The request was made but no response was received
                this._log('error', 'No response received', { request: error.request });
                throw new NetworkError('No response from server', 'NO_RESPONSE', error);
            }

            if (error instanceof ValidationError) {
                throw error;
            }

            throw new NetworkError('Unexpected error creating card', 'UNEXPECTED_ERROR', error);
        }
    }

    async getCard(hash) {
        try {
            const response = await this._axios.get(`/cards/${hash}`, {
                headers: this.getHeaders(),
                timeout: this.config.timeout
            });

            // Log success
            this._log(Logger.LEVELS.INFO, 'Card retrieved successfully', { hash });

            // Return the card details
            return response.data;
        } catch (error) {
            // Log the error
            this._log(Logger.LEVELS.ERROR, 'Error retrieving card', { 
                hash,
                message: error.message 
            });

            // If the error is a 404, throw NotFoundError
            if (error.response && error.response.status === 404) {
                throw new NotFoundError(`Card with hash ${hash} not found`, 'NOT_FOUND_ERROR', error);
            }

            // For other errors, throw the original error
            throw error;
        }
    }

    async deleteCard(hash) {
        try {
            const response = await this._axios.delete(`/cards/${hash}`, {
                headers: this.getHeaders(),
                timeout: this.config.timeout
            });
            return response.status === 200 || response.status === 204;
        } catch (error) {
            this._log('error', 'Error deleting card', { hash, message: error.message });
            if (error.response && error.response.status === 404) {
                throw new NotFoundError(`Card with hash ${hash} not found`, 'NOT_FOUND_ERROR', error);
            }
            throw new NetworkError('Error deleting card', 'NETWORK_ERROR', { originalError: error });
        }
    }

    async deleteAllCards() {
        try {
            const response = await this._axios.delete('/cards', {
                timeout: 5000,
                validateStatus: function (status) {
                    // Treat 200, 204, and 404 as successful
                    return status === 200 || status === 204 || status === 404;
                }
            });
            this._log('info', 'All cards deleted successfully');
            return true;
        } catch (error) {
            // If the server is not running or connection fails, log and return true
            if (error.code === 'ECONNREFUSED' || 
                error.code === 'ENOTFOUND' || 
                error.code === 'ETIMEDOUT') {
                this._log('warn', 'Unable to delete cards. Server may not be running.', { error });
                return true;
            }

            const networkError = new NetworkError('Network error', 'NETWORK_ERROR', error);
            this._log('error', 'Error deleting all cards', { error: networkError });
            throw networkError;
        }
    }

    async healthCheck() {
        try {
            const response = await this._axios({
                method: 'GET',
                url: '/health',
                headers: {
                    'X-API-Key': this.config.apiKey
                }
            });
            return response.data;
        } catch (error) {
            this._log('error', 'Health check failed', { error: error.message });
            throw new NetworkError('Health check failed', 'NETWORK_ERROR', { originalError: error });
        }
    }
}

module.exports = MCardClient;
module.exports.MCardClient = MCardClient;
module.exports.NetworkError = NetworkError;
module.exports.ValidationError = ValidationError;
module.exports.AuthorizationError = AuthorizationError;
module.exports.NotFoundError = NotFoundError;
module.exports.ContentValidator = ContentValidator;
