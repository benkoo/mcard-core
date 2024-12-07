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
    CONTENT_EMPTY: '422: Content cannot be empty',
    CONTENT_TOO_LONG: '422: Content exceeds maximum length',
    INVALID_HASH: '422: Hash is invalid',
    INVALID_HASH_FORMAT: '400: Invalid hash format',
    CONTENT_INVALID: '422: Content is invalid',
    REQUEST_CANCELLED: 'cancelled',
    RATE_LIMIT_EXCEEDED: '429: Rate limit exceeded',
    SERVER_ERROR: '500: Server error',
    NO_RESPONSE: 'No response from server',
    CARD_NOT_FOUND: '404: Card not found',
    TIMEOUT: 'Request timed out',
    CONNECTION_REFUSED: 'Connection refused',
    MALFORMED_RESPONSE: 'Malformed response',
    INVALID_REQUEST: '400: Invalid request',
    UNAUTHORIZED: '401: Unauthorized',
    FORBIDDEN: '403: Forbidden',
    UNKNOWN_ERROR: 'Unknown error',
    NETWORK_ERROR: 'Network error: Unable to reach server',
    DNS_ERROR: 'DNS resolution error: Unable to resolve hostname',
    CONNECTION_ERROR: 'Connection error: Unable to establish connection',
    RETRY_EXHAUSTED: 'Maximum retry attempts exhausted',
    HASH_REQUIRED: 'Hash is required',
    INVALID_PAGE: 'Page number must be greater than 0',
    INVALID_PAGE_SIZE: 'Page size must be between 1 and 100',
    INVALID_SEARCH_PARAMS: 'Invalid search parameters',
    BAD_GATEWAY: '502: Bad Gateway',
    SERVICE_UNAVAILABLE: '503: Service Unavailable',
    GATEWAY_TIMEOUT: '504: Gateway Timeout'
};

class MCardClient {
    constructor(config = {}) {
        this._baseURL = this._normalizeBaseURL(config.baseURL || DEFAULT_BASE_URL);
        this._timeout = config.timeout || DEFAULT_TIMEOUT;
        this._maxRetries = config.maxRetries || MAX_RETRIES;
        this._retryDelay = config.retryDelay || RETRY_DELAY;
        this._maxHistorySize = config.maxHistorySize || 100;
        this._debugMode = config.debug !== undefined ? config.debug : false;
        this._apiKey = config.apiKey || DEFAULT_API_KEY;

        // Initialize metrics
        this._metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            retryAttempts: 0,
            totalResponseTime: 0,
            averageResponseTime: 0
        };
        this._requestHistory = [];

        // Create axios instance with default config
        this._axiosInstance = axios.create({
            baseURL: this._baseURL,
            timeout: this._timeout,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this._apiKey,
                ...(config.headers || {})
            }
        });

        if (this._debugMode) {
            this.log('Initialized MCardClient with config:', {
                baseURL: this._baseURL,
                timeout: this._timeout,
                maxRetries: this._maxRetries,
                retryDelay: this._retryDelay
            });
        }

        // Expose properties for testing
        Object.defineProperties(this, {
            apiKey: { get: () => this._apiKey },
            debug: { get: () => this._debugMode },
            axiosInstance: { get: () => this._axiosInstance }
        });
    }

    async _makeRequest(method, url, data = null, retryCount = 0, cancelToken = null) {
        const startTime = Date.now();
        if (retryCount === 0) {
            this._metrics.totalRequests++;
        }

        try {
            const response = await this._axiosInstance({
                method,
                url,
                data,
                cancelToken
            });

            this._metrics.successfulRequests++;
            const duration = Date.now() - startTime;
            this._metrics.averageResponseTime = 
                (this._metrics.averageResponseTime * (this._metrics.successfulRequests - 1) + duration) / 
                this._metrics.successfulRequests;

            this._addToRequestHistory({
                timestamp: new Date(),
                method,
                url,
                duration,
                success: true,
            });

            return response.data;
        } catch (error) {
            const duration = Date.now() - startTime;

            this._addToRequestHistory({
                timestamp: new Date(),
                method,
                url,
                duration,
                success: false,
                error: error.message
            });

            // Handle request cancellation first, before any retry logic
            if (axios.isCancel(error)) {
                this._metrics.failedRequests++;
                throw new Error(ERROR_MESSAGES.REQUEST_CANCELLED);
            }

            // Handle HTTP errors
            if (error.response) {
                if (error.response.status === 404) {
                    if (error.config.url.includes('/cards/')) {
                        // For GET requests, throw CARD_NOT_FOUND
                        // For DELETE requests, return null
                        if (method === 'DELETE') {
                            return null;
                        }
                        this._metrics.failedRequests++;
                        throw new Error(ERROR_MESSAGES.CARD_NOT_FOUND);
                    }
                    throw new Error(ERROR_MESSAGES.NOT_FOUND);
                }

                // Handle other HTTP errors
                this._metrics.failedRequests++;
                throw new Error(`${error.response.status}: ${error.response.data?.detail || 'Unknown error'}`);
            }

            // Handle DNS resolution errors
            if (error.code === 'ENOTFOUND') {
                if (retryCount >= this._maxRetries) {
                    this._metrics.failedRequests++;
                    throw new Error(ERROR_MESSAGES.RETRY_EXHAUSTED);
                }
                this._metrics.retryAttempts++;
                await new Promise(resolve => setTimeout(resolve, this._retryDelay));
                return this._makeRequest(method, url, data, retryCount + 1, cancelToken);
            }

            // Handle network errors
            if (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET' || error.code === 'ENOTFOUND') {
                this._metrics.failedRequests++;
                throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
            }

            // Check for retry exhaustion for other errors
            if (retryCount >= this._maxRetries) {
                this._metrics.failedRequests++;
                throw new Error(ERROR_MESSAGES.RETRY_EXHAUSTED);
            }

            // Retry for other errors
            this._metrics.retryAttempts++;
            await new Promise(resolve => setTimeout(resolve, this._retryDelay));
            return this._makeRequest(method, url, data, retryCount + 1, cancelToken);
        }
    }

    _addToRequestHistory(request) {
        this._requestHistory.unshift(request);
        if (this._requestHistory.length > this._maxHistorySize) {
            this._requestHistory = this._requestHistory.slice(0, this._maxHistorySize);
        }
    }

    async createCard(params) {
        if (!params || (!params.content && typeof params !== 'string')) {
            throw new Error(ERROR_MESSAGES.CONTENT_INVALID);
        }

        const cardData = {
            content: typeof params === 'string' ? params : params.content,
            metadata: typeof params === 'string' ? {} : params.metadata || {}
        };

        return this._makeRequest('POST', '/cards', cardData);
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
            0,
            cancelToken
        );
        return response;
    }

    async getCard(hash, options = {}) {
        if (!hash) {
            throw new Error(ERROR_MESSAGES.HASH_REQUIRED);
        }
        return this._makeRequest('GET', `/cards/${hash}`);
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
            const response = await this._makeRequest('DELETE', `/cards/${hash}`, null, 0, options.cancelToken);
            return response;
        } catch (error) {
            if (error.message === ERROR_MESSAGES.CARD_NOT_FOUND) {
                return null;
            }
            throw error;
        }
    }

    async checkHealth(cancelToken = null) {
        return this._makeRequest('GET', '/health', null, 0, cancelToken);
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

    getRequestHistory() {
        return this._requestHistory;
    }

    getMetrics() {
        return {
            totalRequests: this._metrics.totalRequests,
            successfulRequests: this._metrics.successfulRequests,
            failedRequests: this._metrics.failedRequests,
            retryAttempts: this._metrics.retryAttempts,
            averageResponseTime: this._metrics.averageResponseTime
        };
    }

    resetMetrics() {
        this._metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            retryAttempts: 0,
            totalResponseTime: 0,
            averageResponseTime: 0
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
