const axios = require('axios');
const dotenv = require('dotenv');

// Constants
const DEFAULT_HOST = 'http://localhost';
const DEFAULT_PORT = 5320;
const DEFAULT_TIMEOUT = 5000;
const DEFAULT_API_KEY = process.env.MCARD_API_KEY || 'dev_key_123';

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
    static LEVELS = {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3
    };

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

    build() {
        return {
            baseURL: this.baseUrl,
            apiKey: this.apiKey,
            timeout: this.timeout,
            debug: this.debug,
            contentValidators: this.contentValidators
        };
    }
}

// Enhanced Content Validator
class ContentValidator {
    validate(content, options = {}) {
        // Convert to string to ensure consistent validation
        const contentStr = content === null || content === undefined 
            ? '' 
            : (typeof content === 'object' 
                ? this.safeStringify(content) 
                : String(content));

        if (!contentStr || contentStr.trim().length === 0) {
            throw new ValidationError('Content cannot be empty', 'VALIDATION_ERROR');
        }
        if (contentStr.length > MCardClient.MAX_CONTENT_LENGTH) {
            throw new ValidationError(`Content cannot exceed ${MCardClient.MAX_CONTENT_LENGTH} characters`, 'VALIDATION_ERROR');
        }
    }

    // Safely stringify objects, handling circular references
    safeStringify(obj, space = 2) {
        const seen = new WeakSet();
        return JSON.stringify(obj, (key, value) => {
            if (typeof value === "object" && value !== null) {
                if (seen.has(value)) {
                    return undefined;
                }
                seen.add(value);
            }
            return value;
        }, space);
    }
}

// MCard Client
class MCardClient {
    static MAX_CONTENT_LENGTH = 1000000;  // Reverted to original test expectation

    constructor(config = {}) {
        const {
            baseURL = 'http://localhost:5320',
            apiKey = null,
            timeout = 5000,
            debug = false,
            logger = null
        } = config;

        this._baseURL = baseURL;
        this._apiKey = apiKey || process.env.MCARD_API_KEY || DEFAULT_API_KEY;
        this._timeout = timeout;
        this._debug = debug;
        this._logger = logger || new Logger(debug ? Logger.LEVELS.DEBUG : Logger.LEVELS.INFO);
        this._axios = axios.create({
            baseURL: this._baseURL,
            timeout: this._timeout,
            headers: {
                'X-API-Key': this._apiKey
            }
        });

        // Add request interceptor to log requests in debug mode
        if (this._debug) {
            this._axios.interceptors.request.use(config => {
                this._log('debug', 'Request Config:', config);
                return config;
            }, error => {
                this._log('error', 'Request Error:', error);
                return Promise.reject(error);
            });
        }

        // Add response interceptor to handle errors more comprehensively
        this._axios.interceptors.response.use(
            response => response,
            error => {
                if (error.response) {
                    switch (error.response.status) {
                        case 401:
                        case 403:
                            this._log('error', 'Authorization Error', error.response.data);
                            throw new AuthorizationError(
                                error.response.data.detail || 'Unauthorized or Forbidden', 
                                'AUTHORIZATION_ERROR', 
                                error
                            );
                        case 404:
                            throw new NotFoundError('Resource not found', 'NOT_FOUND_ERROR', error.response);
                        case 422:
                            throw new ValidationError(
                                error.response.data.detail || 'Invalid request', 
                                'VALIDATION_ERROR', 
                                error
                            );
                        default:
                            throw new NetworkError(
                                `Server error: ${error.response.status}`, 
                                'NETWORK_ERROR', 
                                error
                            );
                    }
                } else if (error.request) {
                    // Request was made but no response received
                    throw new NetworkError('No response from server', 'NETWORK_ERROR', error);
                } else {
                    // Something happened in setting up the request
                    throw new NetworkError('Error setting up request', 'NETWORK_ERROR', error);
                }
            }
        );
    }

    safeStringify(obj) {
        try {
            return JSON.stringify(obj);
        } catch (error) {
            return String(obj);
        }
    }

    _log(level, message, data = null) {
        // Use custom logger if provided, otherwise use default console logging
        const logger = this._logger || console;
        
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

    validator(content) {
        // Handle different content types
        if (content === null || content === undefined) {
            throw new ValidationError('Content cannot be empty', 'VALIDATION_ERROR');
        }

        let contentStr;
        if (typeof content === 'object') {
            try {
                contentStr = this.safeStringify(content);
            } catch (error) {
                throw new ValidationError('Failed to stringify object', 'VALIDATION_ERROR', { originalError: error });
            }
        } else {
            contentStr = String(content);
        }

        // Trim and validate non-empty content
        if (contentStr.trim().length === 0) {
            throw new ValidationError('Content cannot be empty', 'VALIDATION_ERROR');
        }

        // More strict content length validation
        const maxLength = this.constructor.MAX_CONTENT_LENGTH;
        const contentLength = contentStr.length;

        // Stricter validation without tolerance
        if (contentLength > maxLength) {
            throw new ValidationError(
                `Content exceeds maximum length of ${maxLength} characters`, 
                'VALIDATION_ERROR',
                { 
                    contentLength, 
                    maxLength
                }
            );
        }

        return contentStr;
    }

    async getCard(hash) {
        try {
            const response = await this._axios.get(`/cards/${hash}`);
            this._log('info', 'Card retrieved successfully', { hash });
            return response.data;
        } catch (error) {
            if (error.response) {
                const statusCode = error.response.status;
                
                switch(statusCode) {
                    case 404:
                        // Directly throw NotFoundError for 404 cases
                        const notFoundError = new NotFoundError(
                            `Card with hash ${hash} not found`, 
                            'NOT_FOUND_ERROR', 
                            { 
                                hash, 
                                statusCode 
                            }
                        );
                        this._log('error', 'Card not found', { hash });
                        throw notFoundError;
                    case 401:
                    case 403:
                        const authError = new AuthorizationError(
                            'Unauthorized or Forbidden', 
                            'AUTHORIZATION_ERROR', 
                            { 
                                originalError: error 
                            }
                        );
                        this._log('error', 'Authorization error', { error: authError });
                        throw authError;
                    default:
                        const networkError = new NetworkError(
                            `Server error: ${error.response.status}`, 
                            'NETWORK_ERROR', 
                            { 
                                statusCode, 
                                originalError: error 
                            }
                        );
                        this._log('error', 'Network error', { error: networkError });
                        throw networkError;
                }
            } else if (error.request) {
                // Request was made but no response received
                const networkError = new NetworkError(
                    'No response from server', 
                    'NETWORK_ERROR', 
                    { originalError: error }
                );
                this._log('error', 'No server response', { error: networkError });
                throw networkError;
            } else {
                // Something happened in setting up the request
                const notFoundError = new NotFoundError(
                    'Error retrieving card', 
                    'NOT_FOUND_ERROR', 
                    { originalError: error }
                );
                this._log('error', 'Request setup error', { error: notFoundError });
                throw notFoundError;
            }
        }
    }

    async listCards(options = {}) {
        const {
            page = 1,
            pageSize = 10,
            search = '',
            query = search,  // Support both 'search' and 'query'
            searchContent = true,
            searchHash = false,
            searchTime = false
        } = options;

        try {
            const response = await this._axios.get('/cards', {
                params: {
                    page,
                    page_size: pageSize,
                    search: query,
                    search_content: searchContent,
                    search_hash: searchHash,
                    search_time: searchTime
                }
            });

            // Normalize the response to match the expected structure
            const result = {
                cards: response.data.cards || response.data.items || [],
                totalCards: response.data.total_cards || response.data.total || 0,
                totalPages: response.data.total_pages || Math.ceil((response.data.total_cards || 0) / pageSize) || 1,
                currentPage: response.data.current_page || page
            };

            this._log('info', 'Cards listed successfully', {
                totalCards: result.totalCards,
                totalPages: result.totalPages,
                currentPage: result.currentPage
            });

            return result;
        } catch (error) {
            if (error.response && error.response.status === 404) {
                // If no cards found, return an empty list
                return {
                    cards: [],
                    totalCards: 0,
                    totalPages: 0,
                    currentPage: page
                };
            }
            throw new NetworkError('Failed to list cards', 'NETWORK_ERROR', { originalError: error });
        }
    }

    async createCard(content, metadata = {}) {
        try {
            const validatedContent = this.validator(content);
            const payload = { 
                content: validatedContent, 
                metadata: metadata || {} 
            };

            this._log('debug', 'Creating card', { payload });

            const response = await this._axios.post('/cards', payload);
            const cardData = response.data;

            this._log('info', 'Card created successfully', { hash: cardData.hash });
            return cardData;
        } catch (error) {
            if (error instanceof ValidationError) {
                throw error;
            }
            
            const networkError = new NetworkError('Failed to create card', 'NETWORK_ERROR', { originalError: error });
            this._log('error', 'Network error', { error: networkError });
            throw networkError;
        }
    }

    async deleteCard(hash) {
        try {
            console.log(`Attempting to delete card with hash: ${hash}`);
            const response = await this._axios.delete(`/cards/${hash}`);
            console.log(`Delete response status: ${response.status}`);
            this._log('info', `Card deleted successfully: ${hash}`);
            return true; // Return true for successful deletion
        } catch (error) {
            const statusCode = error.response ? error.response.status : null;
            console.log(`Delete error status code: ${statusCode}`);
            
            switch(statusCode) {
                case 404:
                case 204:
                case 403:
                    // Log the error before returning true
                    this._log('info', `Card not found or already deleted: ${hash}`);
                    // Return true for these status codes
                    return true;
                case 401:
                    throw new AuthorizationError('Unauthorized', 'AUTHORIZATION_ERROR', error);
                default:
                    // For other errors, rethrow or handle as needed
                    throw error;
            }
        }
    }

    async deleteAllCards() {
        try {
            const response = await this._axios.delete('/cards');
            this._log('info', 'All cards deleted successfully');
            return true;
        } catch (error) {
            if (error.response) {
                const statusCode = error.response.status;
                
                switch(statusCode) {
                    case 401:
                    case 403:
                        this._log('warn', 'Could not delete all cards: Not authorized', error);
                        return false;
                    default:
                        throw new NetworkError(`Server error: ${error.response.status}`, 'NETWORK_ERROR', error);
                }
            }

            throw new NetworkError('Network error', 'NETWORK_ERROR', error);
        }
    }
}

module.exports = {
    MCardClient,
    MCardError,
    NetworkError,
    ValidationError,
    AuthorizationError,
    NotFoundError,
    Logger,
    ContentValidator,
    MCardClientConfig
};
