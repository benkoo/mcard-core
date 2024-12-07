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
            averageResponseTime: 0,
            networkErrors: 0,
            otherErrors: 0
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

    async _makeRequest(method, endpoint, data = null, cancelToken = null) {
        let retryCount = 0;
        let lastError = null;
        this._metrics.totalRequests++;

        while (true) {
            try {
                const startTime = Date.now();
                const result = await this._axiosInstance({
                    method,
                    url: endpoint,
                    data,
                    cancelToken
                });
                
                const duration = Date.now() - startTime;
                this._metrics.successfulRequests++;
                this._metrics.totalResponseTime += duration;
                this._metrics.averageResponseTime = this._metrics.totalResponseTime / this._metrics.totalRequests;
                
                // Always track request history, not just in debug mode
                this._addToRequestHistory({
                    method,
                    url: endpoint,
                    duration,
                    status: result.status,
                    success: true,
                    data: result.data
                });

                return result.data;
            } catch (error) {
                lastError = error;
                
                // Handle cancellation immediately
                if (axios.isCancel(error)) {
                    this._metrics.failedRequests++;
                    throw new Error(ERROR_MESSAGES.REQUEST_CANCELLED);
                }

                // Always track failed requests
                this._addToRequestHistory({
                    method,
                    url: endpoint,
                    duration: 0,
                    status: error.response?.status || 0,
                    error: error.message,
                    success: false
                });

                if (retryCount >= this._maxRetries) {
                    this._metrics.failedRequests++;
                    
                    if (error.response) {
                        const status = error.response.status;
                        switch (status) {
                            case 422:
                                throw new Error('422: Content is invalid');
                            case 404:
                                throw new Error('404: Card not found');
                            case 403:
                                throw new Error('403: Invalid API key');
                            default:
                                throw new Error(`${status}: ${error.response.data.detail || 'Unknown error'}`);
                        }
                    } else if (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET') {
                        this._metrics.networkErrors++;
                        throw new Error('Network error: Unable to reach server');
                    } else if (error.code === 'ENOTFOUND') {
                        this._metrics.networkErrors++;
                        throw new Error('Maximum retry attempts exhausted');
                    } else if (error.code === 'ETIMEDOUT' || error.message.includes('timeout')) {
                        this._metrics.networkErrors++;
                        throw new Error('Maximum retry attempts exhausted');
                    }

                    this._metrics.otherErrors++;
                    throw new Error('Maximum retry attempts exhausted');
                }

                // Only increment retry attempts if we're actually going to retry
                this._metrics.retryAttempts++;
                await new Promise(resolve => setTimeout(resolve, this._retryDelay));
                retryCount++;
            }
        }
    }

    async createCard(content) {
        if (!content) {
            throw new Error('422: Content is invalid');
        }
        let contentToSend = content;
        let metadata = {};

        if (content && typeof content === 'object' && 'content' in content) {
            contentToSend = content.content;
            metadata = content.metadata || {};
        }

        try {
            const response = await this._makeRequest('POST', '/cards', {
                content: contentToSend,
                metadata: metadata
            });

            // Ensure we have a hash in the response
            if (!response || !response.hash) {
                throw new Error('Server response missing hash');
            }

            return response;
        } catch (error) {
            if (error.response && error.response.status === 422) {
                throw new Error('422: Content is invalid');
            }
            throw error;
        }
    }

    async getCard(hash) {
        if (!hash) {
            throw new Error('Hash is required');
        }
        // Return the server response directly to ensure we use server's metadata
        return await this._makeRequest('GET', `/cards/${hash}`);
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
        return this._makeRequest('GET', '/health', null, cancelToken);
    }

    _addToRequestHistory(request) {
        this._requestHistory.push(request);
        if (this._requestHistory.length > this._maxHistorySize) {
            this._requestHistory.shift();
        }
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
        return [...this._requestHistory];
    }

    getMetrics() {
        return {
            totalRequests: this._metrics.totalRequests,
            successfulRequests: this._metrics.successfulRequests,
            failedRequests: this._metrics.failedRequests,
            retryAttempts: this._metrics.retryAttempts,
            averageResponseTime: this._metrics.averageResponseTime,
            networkErrors: this._metrics.networkErrors,
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
            otherErrors: 0
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
