const axios = require('axios');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Constants
const DEFAULT_TIMEOUT = 5000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;
const RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504];
const DEFAULT_PORT = 5320;
const DEFAULT_HOST = 'http://localhost';
const DEFAULT_BASE_URL = `${DEFAULT_HOST}:${DEFAULT_PORT}`;
const DEFAULT_API_KEY = 'dev_key_123';

// Error messages
const ERROR_MESSAGES = {
    API_KEY_REQUIRED: 'API key is required',
    INVALID_API_KEY: '403: Invalid API key',
    CONTENT_REQUIRED: '422: Content cannot be null or undefined',
    NETWORK_ERROR: 'Network error: Unable to reach server',
    RETRY_EXHAUSTED: 'Request failed after retries',
    CARD_NOT_FOUND: '404: Card not found',
    CONTENT_INVALID: '422: Content is invalid',
    REQUEST_CANCELLED: 'Request was cancelled',
    HASH_REQUIRED: 'Hash is required',
    INVALID_PAGE: 'Invalid page number',
    INVALID_PAGE_SIZE: 'Invalid page size'
};

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
                this._metrics.lastError = ERROR_MESSAGES.CONTENT_INVALID;
                const validationError = new Error(ERROR_MESSAGES.CONTENT_INVALID);
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
                const serverError = new Error(`500: ${error.response.data.detail || 'Server error'}`);
                serverError.status = 500;
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

class MCardClient {
    constructor(config = {}) {
        const defaultConfig = {
            baseURL: 'http://localhost:5320',
            timeout: 2000,
            maxRetries: 3,
            retryDelay: 500,
            debug: false
        };

        this._config = { ...defaultConfig, ...config };
        this._baseURL = this._config.baseURL;
        this._timeout = this._config.timeout;
        this._maxRetries = this._config.maxRetries;
        this._retryDelay = this._config.retryDelay;
        this._debugMode = this._config.debug;

        // Initialize request history
        this._requestHistory = [];

        // Create axios instance with default config
        this._axiosInstance = axios.create({
            baseURL: this._baseURL,
            timeout: this._timeout,
            headers: {
                'X-API-Key': process.env.MCARD_API_KEY || 'dev_key_123'
            }
        });

        // Initialize metrics
        this._metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            retryAttempts: 0,
            totalResponseTime: 0,
            averageResponseTime: 0,
            networkErrors: 0,
            notFoundErrors: 0,
            validationErrors: 0,
            authErrors: 0,
            otherErrors: 0,
            errors: 0,
            lastError: null,
            requestHistory: []
        };

        // Initialize error handlers
        this._networkErrorHandler = new NetworkErrorHandler(this._metrics);
        this._contentErrorHandler = new ContentErrorHandler(this._metrics);

        // Bind methods
        this.log = this.log.bind(this);
        this._normalizeBaseURL = this._normalizeBaseURL.bind(this);
        this._addToRequestHistory = this._addToRequestHistory.bind(this);
        this.getMetrics = this.getMetrics.bind(this);
        this.resetMetrics = this.resetMetrics.bind(this);
    }

    async _makeRequest(method, url, data = null, config = {}) {
        // Always increment total requests
        this._metrics.totalRequests++;

        const startTime = Date.now();
        const requestHistoryEntry = {
            method,
            url,
            timestamp: startTime,
            success: false,
            status: null,
            duration: 0
        };

        try {
            const response = await this._axiosInstance({
                method,
                url,
                data,
                ...config,
                timeout: this._timeout
            });

            const duration = Date.now() - startTime;
            this._metrics.totalResponseTime += duration;
            this._metrics.averageResponseTime = 
                this._metrics.totalRequests > 0 
                ? this._metrics.totalResponseTime / this._metrics.totalRequests 
                : 0;
            this._metrics.successfulRequests++;

            // Update request history entry
            requestHistoryEntry.success = true;
            requestHistoryEntry.status = response.status;
            requestHistoryEntry.duration = duration;
            this._addToRequestHistory(requestHistoryEntry);

            return response.data;
        } catch (error) {
            // Track failed requests only if no error handler handles the error
            let errorHandled = false;

            // If it's a network error, use network error handler
            if (this._networkErrorHandler.isNetworkError(error)) {
                this._networkErrorHandler.handleNetworkError(error);
                errorHandled = true;
            }

            // If it's an HTTP error, use content error handler
            if (error.response) {
                this._contentErrorHandler.handleContentError(error);
                errorHandled = true;
            }

            // Only increment failed requests if no error handler handled the error
            if (!errorHandled) {
                this._metrics.failedRequests++;
            }

            // Update request history entry
            requestHistoryEntry.status = error.response ? error.response.status : 'error';
            this._addToRequestHistory(requestHistoryEntry);

            // Throw the original error
            throw error;
        }
    }

    async createCard(content) {
        if (!content) {
            throw new Error(ERROR_MESSAGES.CONTENT_REQUIRED);
        }
        let contentToSend = content;
        let metadata = {};

        // Handle object input with content and metadata
        if (content && typeof content === 'object') {
            // If it's a JSON object or has a 'binary' key
            if (Object.keys(content).length > 0) {
                // Convert object to JSON string if it's a complex object
                contentToSend = typeof content === 'object' 
                    ? JSON.stringify(content) 
                    : content;
            } else {
                throw new Error(ERROR_MESSAGES.CONTENT_INVALID);
            }
        }

        return this._makeRequest('POST', '/cards', { content: contentToSend, metadata });
    }

    async getCard(hash) {
        if (!hash) {
            throw new Error('Hash is required');
        }
        
        const response = await this._makeRequest('GET', `/cards/${hash}`);
        
        // Return complete response with server metadata
        return response;
    }

    async listCards({ page = 1, pageSize = 10, search = '' } = {}, cancelToken = null) {
        if (page < 1) {
            throw new Error(ERROR_MESSAGES.INVALID_PAGE);
        }
        if (pageSize < 1 || pageSize > 100) {
            throw new Error(ERROR_MESSAGES.INVALID_PAGE_SIZE);
        }
        
        const response = await this._makeRequest(
            'GET',
            `/cards?page=${page}&page_size=${pageSize}&search=${search}`,
            null,
            cancelToken
        );
        return response;
    }

    async getAllCards() {
        const allCards = [];
        let page = 1;
        let hasMore = true;

        while (hasMore) {
            const response = await this.listCards({ page, pageSize: 100 });  // Use larger page size for efficiency
            if (!response || !response.items || response.items.length === 0) {
                hasMore = false;
            } else {
                allCards.push(...response.items);
                if (!response.has_next) {  // Use server's pagination info
                    hasMore = false;
                } else {
                    page++;
                }
            }
        }

        return allCards;
    }

    async deleteCard(hash, options = {}) {
        if (!hash) {
            throw new Error(ERROR_MESSAGES.HASH_REQUIRED);
        }

        try {
            const response = await this._makeRequest('DELETE', `/cards/${hash}`, null, options.cancelToken);
            return response;
        } catch (error) {
            if (error.message === ERROR_MESSAGES.CARD_NOT_FOUND) {
                return null;
            }
            throw error;
        }
    }

    async checkHealth(cancelToken = null) {
        try {
            const config = cancelToken ? { cancelToken } : {};
            const response = await this._makeRequest('GET', '/health', null, config);
            return response;
        } catch (error) {
            // If it's a network error, handle it
            if (this._networkErrorHandler.isNetworkError(error)) {
                this._networkErrorHandler.handleNetworkError(error);
            }
            throw error;
        }
    }

    _addToRequestHistory(entry) {
        const historyEntry = {
            ...entry,
            timestamp: entry.timestamp || new Date().toISOString()
        };

        // Always track request history, regardless of debug mode
        this._requestHistory.push(historyEntry);

        // Limit history size if needed
        if (this._requestHistory.length > 100) {
            this._requestHistory.shift();
        }
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
        return {
            totalRequests: this._metrics.totalRequests,
            successfulRequests: this._metrics.successfulRequests,
            failedRequests: this._metrics.failedRequests,
            retryAttempts: this._metrics.retryAttempts,
            totalResponseTime: this._metrics.totalResponseTime || 0,
            averageResponseTime: this._metrics.averageResponseTime || 0,
            networkErrors: this._metrics.networkErrors,
            notFoundErrors: this._metrics.notFoundErrors,
            validationErrors: this._metrics.validationErrors,
            authErrors: this._metrics.authErrors,
            otherErrors: this._metrics.otherErrors
        };
    }

    resetMetrics() {
        this._metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            retryAttempts: 0,
            totalResponseTime: 0,
            averageResponseTime: 0,
            networkErrors: 0,
            notFoundErrors: 0,
            validationErrors: 0,
            authErrors: 0,
            otherErrors: 0,
            errors: 0,
            lastError: null,
            requestHistory: []
        };
        this._requestHistory = [];
    }

    log(...args) {
        if (this._debugMode) {
            console.log(...args);
        }
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
