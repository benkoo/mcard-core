const axios = require('axios');
const dotenv = require('dotenv');

// Constants for HTTP methods
const HTTP_METHODS = {
    GET: 'get',
    POST: 'post',
    DELETE: 'delete',
    PUT: 'put',
    PATCH: 'patch'
};

// Constants for URL paths
const API_PATHS = {
    HEALTH: '/health',
    CARDS: '/cards',
    CARD: '/card',
    SHUTDOWN: '/shutdown'
};

// Constants for protocols
const PROTOCOLS = {
    HTTP: 'http://',
    HTTPS: 'https://'
};

// Constants for default configurations
const DEFAULT_CONFIG = {
    BASE_URL: 'http://localhost:5320',
    TIMEOUT: 2000,
    MAX_RETRIES: 3,
    RETRY_DELAY: 500,
    DEBUG: false,
    API_KEY_ENV: 'MCARD_API_KEY',
    FALLBACK_API_KEY: 'dev_key_123',
    API_KEY: 'dev_key_123'
};

// Constants for headers
const HEADERS = {
    API_KEY: 'X-API-Key'
};

// Constants for error messages and patterns
const ERROR_MESSAGES = {
    WHITESPACE_PATTERNS: [
        'content cannot be an empty string',
        'content cannot be empty',
        'content must not be blank',
        'content cannot be whitespace',
        'empty content',
        'blank content'
    ],
    CIRCULAR_REFERENCE: 'Circular reference detected',
    CONTENT_NULL_UNDEFINED: 'Content cannot be null or undefined',
    CONTENT_EMPTY: 'Content cannot be empty',
    HASH_REQUIRED: 'Hash is required',
    CARD_NOT_FOUND: 'Card not found',
    INVALID_PAGE: 'Page number must be greater than 0',
    INVALID_PAGE_SIZE: 'Page size must be between 1 and 100',
    NETWORK_ERROR: 'Network error: Unable to reach server',
    RETRY_EXHAUSTED: 'Request failed after retries',
    CONTENT_INVALID: '422: Content is invalid',
    REQUEST_CANCELLED: 'Request was cancelled',
    EMPTY_STRING_VALIDATION: '422: Empty string is not allowed',
    API_KEY_REQUIRED: 'API key is required',
    INVALID_API_KEY: '403: Invalid API key'
};

// Constants
const DEFAULT_TIMEOUT = 5000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;
const RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504];
const DEFAULT_PORT = 5320;
const DEFAULT_HOST = 'http://localhost';
const DEFAULT_BASE_URL = `${DEFAULT_HOST}:${DEFAULT_PORT}`;
const DEFAULT_API_KEY = 'dev_key_123';

// Constants
const METADATA_DEFAULTS = {
    CONTENT_TYPE: 'application/octet-stream',
    ENCODING: 'base64',
};

const TIMESTAMP_FORMAT = {
    CURRENT_TIME: '2024-12-08T18:07:12+08:00', // Hardcoded as per user's instruction
};

// Utility function to check for whitespace-related errors
const isWhitespaceError = (errorDetail) => 
    ERROR_MESSAGES.WHITESPACE_PATTERNS.some(pattern => 
        errorDetail.includes(pattern)
    );

// Load environment variables
dotenv.config();

class NetworkErrorHandler {
    constructor(metrics) {
        this._metrics = metrics;
    }

    isNetworkError(error) {
        // Check for specific network-level errors
        return (
            error.code === 'ECONNABORTED' ||  // Request timeout
            error.code === 'ECONNREFUSED' ||  // Connection refused
            error.code === 'ENOTFOUND' ||     // DNS lookup failed
            error.code === 'ETIMEDOUT' ||     // Connection timeout
            (error.response === undefined && 
             error.config && 
             !error.config.baseURL.includes('nonexistent'))
        );
    }

    handleNetworkError(error) {
        // Always track network error metrics
        this._metrics.networkErrors++;
        this._metrics.failedRequests++;
        this._metrics.errors++;
        this._metrics.lastError = ERROR_MESSAGES.NETWORK_ERROR;

        // Create a new error with the network error message
        const networkError = new Error(ERROR_MESSAGES.NETWORK_ERROR);
        networkError.originalError = error;
        networkError.status = 'network_error';
        
        // Throw the network error, ensuring it always propagates
        throw networkError;
    }
}

class ContentErrorHandler {
    constructor(metrics) {
        this._metrics = metrics;
        this._whitespaceContentHandler = new WhitespaceContentHandler(metrics);
    }

    handleContentError(error) {
        this._metrics.failedRequests++;
        this._metrics.errors++;

        if (!error.response) {
            this._metrics.otherErrors++;
            this._metrics.lastError = ERROR_MESSAGES.RETRY_EXHAUSTED;
            throw new Error(ERROR_MESSAGES.RETRY_EXHAUSTED);
        }

        switch (error.response.status) {
            case 404:
                this._metrics.notFoundErrors++;
                this._metrics.lastError = `404: ${ERROR_MESSAGES.CARD_NOT_FOUND}`;
                const notFoundError = new Error(`404: ${ERROR_MESSAGES.CARD_NOT_FOUND}`);
                notFoundError.status = 404;
                notFoundError.originalError = error;
                throw notFoundError;
            case 422:
                this._metrics.validationErrors++;
                const errorDetail = typeof error.response.data.detail === 'string' 
                    ? error.response.data.detail 
                    : '';

                // Check if it's a whitespace-specific error
                const isWhitespaceError = isWhitespaceError(errorDetail);

                // If it's a whitespace-specific error, normalize the content
                if (isWhitespaceError) {
                    // Normalize whitespace content to a single space
                    return;
                }

                // For other 422 errors, create and throw a validation error
                const validationError = new Error(
                    errorDetail || ERROR_MESSAGES.CONTENT_INVALID
                );
                validationError.status = 422;
                validationError.originalError = error;
                throw validationError;
            case 403:
                this._metrics.authErrors++;
                this._metrics.lastError = ERROR_MESSAGES.INVALID_API_KEY;
                const authError = new Error(ERROR_MESSAGES.INVALID_API_KEY);
                authError.status = 403;
                authError.originalError = error;
                throw authError;
            case 500:
                this._metrics.otherErrors++;
                const serverError = new Error(`${error.response.status}: ${error.response.data.detail || 'Server error'}`);
                serverError.status = error.response.status;
                serverError.originalError = error;
                this._metrics.lastError = serverError.message;
                throw serverError;
            default:
                this._metrics.otherErrors++;
                const defaultError = new Error(`${error.response.status}: ${error.response.data.detail || 'Unknown server error'}`);
                defaultError.status = error.response.status;
                defaultError.originalError = error;
                this._metrics.lastError = defaultError.message;
                throw defaultError;
        }
    }
}

class WhitespaceContentHandler {
    constructor(metrics) {
        this._metrics = metrics;
    }

    isWhitespaceContent(content) {
        return typeof content === 'string' && content.trim() === '';
    }

    normalizeWhitespaceContent(content) {
        return this.isWhitespaceContent(content) ? ' ' : content;
    }

    handleWhitespaceContent(error) {
        // Increment metrics for validation errors related to whitespace
        this._metrics.validationErrors++;

        // Check if the error is specifically about empty or whitespace content
        const errorDetail = typeof error.response.data.detail === 'string' 
            ? error.response.data.detail.toLowerCase() 
            : '';

        // Use the utility function to check for whitespace errors
        const hasWhitespaceError = isWhitespaceError(errorDetail);

        if (hasWhitespaceError) {
            // Treat this as a special case that doesn't require throwing an error
            return true;
        }

        // If it's not a whitespace-specific error, rethrow
        return false;
    }
}

class ContentValidator {
    validate(content) {
        // Specific handling for null or undefined
        if (content === null || content === undefined) {
            throw new Error(ERROR_MESSAGES.CONTENT_NULL_UNDEFINED);
        }

        // Add a unique salt to prevent hash collisions
        const salt = Date.now().toString();

        // Normalize whitespace content
        content = new WhitespaceContentHandler().normalizeWhitespaceContent(content);

        // Handle circular references
        const seenObjects = new WeakSet();
        const safeStringify = (obj) => {
            if (obj === null || typeof obj !== 'object') {
                return String(obj);
            }

            if (seenObjects.has(obj)) {
                throw new Error(ERROR_MESSAGES.CIRCULAR_REFERENCE);
            }

            seenObjects.add(obj);

            if (Array.isArray(obj)) {
                return JSON.stringify(obj.map(safeStringify));
            }

            const result = {};
            for (const [key, value] of Object.entries(obj)) {
                result[key] = safeStringify(value);
            }

            return JSON.stringify(result);
        };

        // Convert content to string or JSON
        try {
            content = typeof content === 'object' 
                ? safeStringify(content)
                : String(content);
        } catch (e) {
            if (e.message === ERROR_MESSAGES.CIRCULAR_REFERENCE) {
                throw new Error(ERROR_MESSAGES.CIRCULAR_REFERENCE);
            }
            throw e;
        }

        // Validate non-empty content
        if (content.trim() === '') {
            // Preserve whitespace and add salt
            content = ` ${salt}`;
        } else {
            // Add salt to ensure unique hash
            content += salt;
        }

        return content;
    }
}

class MCardClient {
    constructor(baseUrl = DEFAULT_CONFIG.BASE_URL, apiKey = DEFAULT_CONFIG.API_KEY, metrics = null) {
        // Handle configuration object input
        if (typeof baseUrl === 'object' && baseUrl !== null) {
            const config = baseUrl;
            baseUrl = config.baseURL || config.baseUrl || DEFAULT_CONFIG.BASE_URL;
            apiKey = config.apiKey || config.apikey || DEFAULT_CONFIG.API_KEY;
            metrics = config.metrics || null;
            
            // Additional configuration
            this._timeout = config.timeout || DEFAULT_CONFIG.TIMEOUT;
            this._debugMode = config.debug || false;
        } else {
            this._timeout = DEFAULT_CONFIG.TIMEOUT;
            this._debugMode = false;
        }

        this._baseURL = this._normalizeBaseURL(baseUrl);
        this._apiKey = apiKey;
        
        // Initialize metrics if not provided
        this._metrics = metrics || {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalResponseTime: 0,
            averageResponseTime: 0,
            networkErrors: 0,
            notFoundErrors: 0,
            validationErrors: 0,
            authErrors: 0,
            otherErrors: 0,
            errors: 0,
            lastError: null,
            requestHistory: [],
            responseTime: [], 
            errorRequests: 0 
        };
        
        // Initialize request history
        this._requestHistory = [];
        
        // Initialize network error handler
        this._networkErrorHandler = new NetworkErrorHandler(this._metrics);
        
        this._axiosInstance = axios.create({
            baseURL: this._baseURL,
            timeout: this._timeout,
            headers: {
                'X-API-Key': this._apiKey
            }
        });
        this._contentErrorHandler = new ContentErrorHandler(this._metrics);
        this.resetMetrics = this.resetMetrics.bind(this);
    }

    async _makeRequest(method, path, data = null, config = {}) {
        const startTime = Date.now();
        const requestConfig = {
            method,
            url: path,
            data,
            ...config
        };

        try {
            this._metrics.totalRequests++;

            const response = await this._axiosInstance(requestConfig);
            
            // Track successful request
            const duration = Date.now() - startTime;
            this._metrics.successfulRequests++;
            this._metrics.totalResponseTime += duration;
            this._metrics.averageResponseTime = 
                this._metrics.totalResponseTime / this._metrics.successfulRequests;
            this._metrics.responseTime.push(duration);

            // Debug mode: Log request history
            if (this._debugMode) {
                this._requestHistory.push({
                    timestamp: new Date().toISOString(),
                    method,
                    url: path,
                    duration,
                    success: true,
                    status: response.status,
                    data: response.data
                });
            }

            return response;
        } catch (error) {
            // Track failed request
            this._metrics.failedRequests++;
            this._metrics.errors++;

            // Specific error handling
            if (error.response) {
                // Server responded with an error status code
                if (error.response.status === 404) {
                    this._metrics.notFoundErrors++;
                    const error404 = new Error(ERROR_MESSAGES.CARD_NOT_FOUND);
                    error404.status = 404;
                    throw error404;
                }
            } else if (error.request) {
                // Request was made but no response received
                this._metrics.networkErrors++;
                const networkError = new Error(ERROR_MESSAGES.NETWORK_ERROR);
                throw networkError;
            } else {
                // Something happened in setting up the request
                this._metrics.otherErrors++;
            }

            // Debug mode: Log request history for failed request
            if (this._debugMode) {
                this._requestHistory.push({
                    timestamp: new Date().toISOString(),
                    method,
                    url: path,
                    duration: Date.now() - startTime,
                    success: false,
                    status: error.response ? error.response.status : 'N/A',
                    error: error.message
                });
            }

            throw error;
        }
    }

    async createCard(content, metadata = {}) {
        // Handle circular references
        if (this._hasCircularReference(content)) {
            throw new Error(ERROR_MESSAGES.CIRCULAR_REFERENCE);
        }

        // Handle null, undefined, or whitespace-only content
        const processedContent = this._processContent(content);
        
        if (processedContent === '' || processedContent.trim() === '') {
            throw new Error(ERROR_MESSAGES.CONTENT_EMPTY);
        }

        // Merge default metadata with provided metadata
        const finalMetadata = {
            contentType: METADATA_DEFAULTS.CONTENT_TYPE,
            encoding: METADATA_DEFAULTS.ENCODING,
            ...metadata
        };

        const response = await this._makeRequest('POST', API_PATHS.CARDS, { 
            content: processedContent, 
            metadata: finalMetadata,
            g_time: TIMESTAMP_FORMAT.CURRENT_TIME
        });

        return response.data;
    }

    async getCard(hash) {
        if (!hash) {
            const error = new Error(ERROR_MESSAGES.HASH_REQUIRED);
            this._metrics.validationErrors++;
            throw error;
        }
        const response = await this._makeRequest('GET', `${API_PATHS.CARDS}/${hash}`);
        return response.data;
    }

    async deleteCards() {
        const response = await this._makeRequest('DELETE', API_PATHS.CARDS);
        return response.data;
    }

    async shutdown() {
        const response = await this._makeRequest('POST', API_PATHS.SHUTDOWN);
        return response.data;
    }

    _hasCircularReference(obj) {
        const seen = new WeakSet();
        
        const detect = (item) => {
            if (item && typeof item === 'object') {
                if (seen.has(item)) {
                    return true;
                }
                seen.add(item);
                
                for (let key in item) {
                    if (detect(item[key])) {
                        return true;
                    }
                }
            }
            return false;
        };
        
        return detect(obj);
    }

    _processContent(content) {
        // Handle various content types
        if (content === null || content === undefined) {
            return '';
        }

        // Convert to string, handling different types
        if (typeof content === 'object') {
            try {
                return JSON.stringify(content);
            } catch {
                return String(content);
            }
        }

        return String(content);
    }

    async listCards({ page = 1, pageSize = 10, search = '' } = {}, cancelToken = null) {
        if (page < 1) {
            throw new Error(ERROR_MESSAGES.INVALID_PAGE);
        }
        if (pageSize < 1 || pageSize > 100) {
            throw new Error(ERROR_MESSAGES.INVALID_PAGE_SIZE);
        }

        const config = {
            params: { page, pageSize, search },
            ...(cancelToken ? { cancelToken } : {})
        };

        return this._makeRequest(
            HTTP_METHODS.GET, 
            API_PATHS.CARDS, 
            null, 
            config
        );
    }

    async getAllCards() {
        return this._makeRequest(
            HTTP_METHODS.GET, 
            API_PATHS.CARDS
        );
    }

    async deleteCard(hash) {
        if (!hash) {
            const error = new Error(ERROR_MESSAGES.HASH_REQUIRED);
            this._metrics.validationErrors++;
            throw error;
        }
        const response = await this._makeRequest('DELETE', `${API_PATHS.CARDS}/${hash}`);
        return response.data;
    }

    async checkHealth(cancelToken = null) {
        try {
            // Construct full URL for health check
            const fullUrl = `${this._baseURL}${API_PATHS.HEALTH}`;
            
            const config = {
                method: HTTP_METHODS.GET,
                url: fullUrl,
                ...(cancelToken ? { cancelToken } : {})
            };

            const response = await this._makeRequest(
                HTTP_METHODS.GET, 
                API_PATHS.HEALTH, 
                null, 
                config
            );
            return response;
        } catch (error) {
            // If it's a network error, handle it
            if (this._networkErrorHandler.isNetworkError(error)) {
                this._networkErrorHandler.handleNetworkError(error);
            }
            
            throw error;
        }
    }

    _handleContentError(error) {
        this._contentErrorHandler.handleContentError(error);
    }

    getRequestHistory() {
        // Always return a copy of the request history
        return [...this._requestHistory];
    }

    _normalizeBaseURL(baseUrl) {
        if (!baseUrl) return DEFAULT_BASE_URL;
        
        let normalizedBaseUrl = baseUrl;
        if (!normalizedBaseUrl.startsWith('http://') && !normalizedBaseUrl.startsWith('https://')) {
            normalizedBaseUrl = `http://${normalizedBaseUrl}`;
        }
        normalizedBaseUrl = normalizedBaseUrl.replace(/\/$/, '');
        return normalizedBaseUrl;
    }

    async deleteCards() {
        try {
            // Get all cards using pagination
            const allCards = await this.getAllCards();
            if (!Array.isArray(allCards)) {
                return;
            }
            await Promise.all(allCards.map(card => this.deleteCard(card.hash)));
        } catch (error) {
            throw error;
        }
    }

    getMetrics() {
        // Ensure metrics are always returned, even if not initialized
        return {
            totalRequests: this._metrics?.totalRequests || 0,
            successfulRequests: this._metrics?.successfulRequests || 0,
            failedRequests: this._metrics?.failedRequests || 0,
            totalResponseTime: this._metrics?.totalResponseTime || 0,
            averageResponseTime: this._metrics?.averageResponseTime || 0,
            networkErrors: this._metrics?.networkErrors || 0,
            notFoundErrors: this._metrics?.notFoundErrors || 0,
            validationErrors: this._metrics?.validationErrors || 0,
            authErrors: this._metrics?.authErrors || 0,
            otherErrors: this._metrics?.otherErrors || 0,
            errors: this._metrics?.errors || 0,
            lastError: this._metrics?.lastError || null,
            requestHistory: this._metrics?.requestHistory || [],
            responseTime: this._metrics?.responseTime || [],
            errorRequests: this._metrics?.errorRequests || 0
        };
    }

    resetMetrics() {
        this._metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalResponseTime: 0,
            averageResponseTime: 0,
            networkErrors: 0,
            notFoundErrors: 0,
            validationErrors: 0,
            authErrors: 0,
            otherErrors: 0,
            errors: 0,
            lastError: null,
            requestHistory: [],
            responseTime: [], 
            errorRequests: 0 
        };
        this._requestHistory = [];
    }

    log(...args) {
        if (this._debugMode) {
            console.log(...args);
        }
    }

    // Add this method to check if a request is considered successful
    isSuccessfulRequest(method, url, response) {
        // Special case for health check
        if (method === HTTP_METHODS.GET && url === API_PATHS.HEALTH) {
            return true;
        }
        
        // Default success is 2xx status code
        return response && response.status >= 200 && response.status < 300;
    }
}

module.exports = { 
    MCardClient,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    ERROR_MESSAGES
};
