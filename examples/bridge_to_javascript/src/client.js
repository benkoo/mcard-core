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
    REQUEST_CANCELLED: 'Request cancelled',
    RATE_LIMIT_EXCEEDED: '429: Rate limit exceeded',
    SERVER_ERROR: '500: Server error',
    NO_RESPONSE: 'No response from server',
    CARD_NOT_FOUND: '404: Card not found'
};

class MCardClient {
    constructor(options = {}) {
        // Extract options
        const {
            apiKey = process.env.MCARD_API_KEY,
            baseUrl = DEFAULT_BASE_URL,
            port = DEFAULT_PORT,
            timeout = DEFAULT_TIMEOUT,
            maxRetries = MAX_RETRIES,
            retryDelay = RETRY_DELAY,
            ...config
        } = options;

        // Validate API key
        if (!apiKey || apiKey.trim().length === 0) {
            throw new Error(ERROR_MESSAGES.API_KEY_REQUIRED);
        }
        this.apiKey = apiKey;

        // Normalize base URL: handle protocol, port, and trailing slash
        let normalizedBaseUrl = baseUrl;
        if (!normalizedBaseUrl.startsWith('http')) {
            normalizedBaseUrl = `http://${normalizedBaseUrl}`;
        }
        if (port !== DEFAULT_PORT) {
            const urlObj = new URL(normalizedBaseUrl);
            urlObj.port = port;
            normalizedBaseUrl = urlObj.toString();
        }
        normalizedBaseUrl = normalizedBaseUrl.replace(/\/$/, '');

        // Initialize axios instance with default configuration
        const axiosConfig = {
            baseURL: normalizedBaseUrl,
            timeout,
            validateStatus: null,  // Don't throw on any status
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey
            }
        };

        // Use provided axios instance or create new one
        this.axiosInstance = config._axiosInstance || config.axiosInstance || axios.create(axiosConfig);

        // Performance monitoring
        this._requestHistory = [];
        this._historyLimit = 10;
        this._requestStartTimes = new Map();  // Track start times per request
        this._metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalDuration: 0,
            requestHistory: []
        };
        
        // Cancel tokens
        this._currentCancelTokens = [];

        // Retry configuration
        this.maxRetries = maxRetries;
        this.retryDelay = retryDelay;

        // Add request interceptor for metrics
        this.axiosInstance.interceptors.request.use((config) => {
            config.startTime = Date.now();
            return config;
        });

        // Add response interceptor for metrics
        this.axiosInstance.interceptors.response.use(
            (response) => {
                this._updateMetrics(response.config, true);
                return response;
            },
            (error) => {
                if (error.config) {
                    this._updateMetrics(error.config, false);
                }
                throw error;
            }
        );

        // Add interceptors
        this._addInterceptors();
    }

    _updateMetrics(config, success) {
        // Skip metrics for cleanup operations and GET requests
        if (config.method === 'GET' || (config.url.includes('/cards') && config.method === 'DELETE')) {
            return;
        }

        const duration = Date.now() - config.startTime;
        this._metrics.totalRequests++;
        if (success) {
            this._metrics.successfulRequests++;
        } else {
            this._metrics.failedRequests++;
        }
        this._metrics.totalDuration += duration;
        this._metrics.requestHistory.push({
            method: config.method,
            url: config.url,
            duration,
            success,
            timestamp: new Date().toISOString()
        });

        // Keep history limited to last 100 requests
        if (this._metrics.requestHistory.length > 100) {
            this._metrics.requestHistory.shift();
        }
    }

    /**
     * Get current performance metrics
     * @returns {Object} Current metrics including request counts and history
     */
    getMetrics() {
        return {
            totalRequests: this._metrics.totalRequests,
            successfulRequests: this._metrics.successfulRequests,
            failedRequests: this._metrics.failedRequests,
            totalDuration: this._metrics.totalDuration,
            requestHistory: [...this._metrics.requestHistory]
        };
    }

    /**
     * Reset metrics to initial state
     */
    resetMetrics() {
        this._metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalDuration: 0,
            requestHistory: []
        };
    }

    // Getters and setters for baseURL
    get baseUrl() {
        return this.axiosInstance.defaults.baseURL;
    }

    set baseUrl(url) {
        this.axiosInstance.defaults.baseURL = url;
    }

    // Method to set API key after initialization
    setApiKey(apiKey) {
        if (!apiKey || apiKey.trim().length === 0) {
            throw new Error(ERROR_MESSAGES.API_KEY_REQUIRED);
        }
        this.apiKey = apiKey;
        this.axiosInstance.defaults.headers['X-API-Key'] = apiKey;
    }

    // Helper method to format base URL
    _formatBaseUrl(url) {
        // Add protocol if missing
        if (!/^https?:\/\//i.test(url)) {
            url = `http://${url}`;
        }
        return url;
    }

    // Add interceptors (extracted from constructor for clarity)
    _addInterceptors() {
        // Only add interceptors if they don't already exist
        if (!this.axiosInstance.interceptors.response.handlers?.length) {
            // Add request interceptor for retries
            this.axiosInstance.interceptors.response.use(
                response => {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error(`${response.status}: ${response.data?.detail || 'Invalid API key'}`);
                    }
                    return response;
                },
                async error => {
                    if (!error.config) {
                        return Promise.reject(error);
                    }

                    const retryCount = error.config._retryCount || 0;
                    if (retryCount >= this.maxRetries) {
                        return Promise.reject(error);
                    }

                    const shouldRetry = RETRY_STATUS_CODES.includes(error.response?.status);
                    if (!shouldRetry) {
                        return Promise.reject(error);
                    }

                    error.config._retryCount = retryCount + 1;
                    const delay = this.retryDelay * Math.pow(2, retryCount);
                    
                    await new Promise(resolve => setTimeout(resolve, delay));
                    return this.axiosInstance.request(error.config);
                }
            );
        }

        // Only add performance monitoring interceptors if they don't exist
        if (!this.axiosInstance.interceptors.request.handlers?.length) {
            // Add request interceptor for performance monitoring
            this.axiosInstance.interceptors.request.use(
                (config) => {
                    // Generate unique request ID
                    config._requestId = Math.random().toString(36).substring(7);
                    this._requestStartTimes.set(config._requestId, Date.now());
                    return config;
                },
                (error) => {
                    if (error.config?._requestId) {
                        const startTime = this._requestStartTimes.get(error.config._requestId);
                        this._trackRequest(true, startTime);
                        this._requestStartTimes.delete(error.config._requestId);
                    }
                    return Promise.reject(error);
                }
            );

            // Add response interceptor for performance monitoring
            this.axiosInstance.interceptors.response.use(
                (response) => {
                    const requestId = response.config._requestId;
                    const startTime = this._requestStartTimes.get(requestId);
                    const duration = Date.now() - startTime;
                    this._trackRequest(response.status >= 400, startTime);
                    this._requestStartTimes.delete(requestId);
                    return response;
                },
                (error) => {
                    const requestId = error.config?._requestId;
                    const startTime = requestId ? this._requestStartTimes.get(requestId) : null;
                    if (requestId) {
                        this._trackRequest(true, startTime);
                        this._requestStartTimes.delete(requestId);
                    }
                    return Promise.reject(error);
                }
            );
        }
    }

    /**
     * Create a new card.
     * @param {string|Object} params - Content for the new card or an object with a 'content' property
     * @returns {Promise<Object>} - Created card object
     * @throws {Error} - If content is invalid or server error occurs
     */
    async createCard(params) {
        // Handle both object and direct content parameter
        const content = typeof params === 'object' ? params.content : params;

        // Input validation
        if (content === undefined || content === null) {
            throw new Error(ERROR_MESSAGES.CONTENT_REQUIRED);
        }

        // Convert non-string content to string
        const stringContent = typeof content === 'string' ? content : 
            (content instanceof Buffer ? content.toString() : 
                (typeof content === 'object' ? JSON.stringify(content) : String(content)));

        if (stringContent.trim().length === 0) {
            throw new Error(ERROR_MESSAGES.CONTENT_EMPTY);
        }

        if (stringContent.length > 1000000) {
            throw new Error(ERROR_MESSAGES.CONTENT_TOO_LONG);
        }

        try {
            const response = await this.axiosInstance.post('/cards', { content: stringContent });
            
            // Handle invalid API key error
            if (response.status === 403) {
                throw new Error(ERROR_MESSAGES.INVALID_API_KEY);
            }
            
            return response.data;
        } catch (error) {
            if (error.response?.status === 403) {
                throw new Error(ERROR_MESSAGES.INVALID_API_KEY);
            }
            if (error.code === 'ECONNABORTED') {
                throw new Error(ERROR_MESSAGES.NO_RESPONSE);
            }
            throw error;
        }
    }

    /**
     * Get a card by hash.
     * @param {string} hash - Hash of the card to retrieve.
     * @param {CancelToken} cancelToken - Optional cancel token for the request.
     * @returns {Promise<Object>} - Card object.
     * @throws {Error} - If hash is invalid or server error occurs.
     */
    async getCard(hash) {
        // Validate hash format
        if (!hash || (typeof hash === 'string' && hash.trim().length === 0)) {
            throw new Error(ERROR_MESSAGES.INVALID_HASH_FORMAT);
        }

        try {
            const response = await this.axiosInstance.get(`/cards/${hash}`);
            return response.data;
        } catch (error) {
            throw this._handleError(error);
        }
    }

    async listCards() {
        try {
            const response = await this.axiosInstance.get('/cards');
            return response.data;
        } catch (error) {
            if (error.code === 'ECONNREFUSED') {
                throw new Error(ERROR_MESSAGES.NO_RESPONSE);
            }
            if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
                throw new Error(ERROR_MESSAGES.REQUEST_TIMEOUT);
            }
            if (error.response) {
                switch (error.response.status) {
                    case 401:
                    case 403:
                        throw new Error(ERROR_MESSAGES.INVALID_API_KEY);
                    case 429:
                        throw new Error(ERROR_MESSAGES.RATE_LIMIT_EXCEEDED);
                    case 500:
                        throw new Error(ERROR_MESSAGES.SERVER_ERROR);
                    default:
                        throw new Error(`${error.response.status}: ${error.response.data?.error || 'Unknown error'}`);
                }
            } else if (error.request) {
                if (error.code === 'ECONNABORTED') {
                    throw new Error(ERROR_MESSAGES.REQUEST_TIMEOUT);
                }
                throw new Error(ERROR_MESSAGES.NO_RESPONSE);
            } else {
                throw error;
            }
        }
    }

    async deleteCard(hash) {
        // Validate hash format
        if (!hash || typeof hash !== 'string' || !/^[a-f0-9]{32}$/i.test(hash)) {
            throw new Error(ERROR_MESSAGES.INVALID_HASH_FORMAT);
        }

        try {
            const response = await this.axiosInstance.delete(`/cards/${hash}`);
            if (response.data && response.data.detail === '404: Card not found') {
                throw new Error(ERROR_MESSAGES.CARD_NOT_FOUND);
            }
            return response.data;
        } catch (error) {
            if (error.response && error.response.status === 404) {
                throw new Error(ERROR_MESSAGES.CARD_NOT_FOUND);
            }
            throw error;
        }
    }

    async checkHealth() {
        const startTime = Date.now();
        try {
            const response = await this.axiosInstance.get('/health');

            // Log request time if debug is enabled
            this._logRequestTime('/health', startTime);

            // Validate response structure
            if (!response.data || typeof response.data !== 'object' || !response.data.status) {
                throw new Error(ERROR_MESSAGES.INVALID_RESPONSE);
            }

            // Specific handling for unhealthy status
            if (response.data.status !== 'healthy') {
                throw new Error(ERROR_MESSAGES.SERVER_ERROR);
            }

            return response.data;
        } catch (error) {
            if (error.response) {
                switch (error.response.status) {
                    case 401:
                    case 403:
                        throw new Error('401: Invalid API key');
                    case 500:
                        throw new Error(ERROR_MESSAGES.SERVER_ERROR);
                    default:
                        throw new Error(`${error.response.status}: ${error.response.data?.error || 'Unknown error'}`);
                }
            } else if (error.request) {
                // For network errors (including timeouts), throw a standard error
                throw new Error(ERROR_MESSAGES.NO_RESPONSE);
            } else {
                throw error;
            }
        }
    }

    // Handle error response from the server
    _handleError(error) {
        if (error.response) {
            const status = error.response.status;
            switch (status) {
                case 400:
                    return new Error(ERROR_MESSAGES.INVALID_HASH_FORMAT);
                case 401:
                case 403:
                    return new Error(ERROR_MESSAGES.INVALID_API_KEY);
                case 404:
                    return new Error(ERROR_MESSAGES.CARD_NOT_FOUND);
                case 422:
                    return new Error(ERROR_MESSAGES.CONTENT_INVALID);
                case 429:
                    return new Error(ERROR_MESSAGES.RATE_LIMIT_EXCEEDED);
                case 500:
                    return new Error(ERROR_MESSAGES.SERVER_ERROR);
                default:
                    return new Error(`${status}: ${error.response.data.detail || 'Unknown error'}`);
            }
        }

        if (error.code === 'ECONNREFUSED' || error.code === 'ECONNABORTED') {
            return new Error(ERROR_MESSAGES.NO_RESPONSE);
        }

        if (axios.isCancel(error)) {
            return new Error(ERROR_MESSAGES.REQUEST_CANCELLED);
        }

        return error;
    }

    // Process API response
    _processResponse(response) {
        if (!response || !response.data) {
            throw new Error(ERROR_MESSAGES.INVALID_RESPONSE);
        }

        // For card responses, ensure content is properly handled
        if (response.data.content !== undefined) {
            const content = response.data.content;
            // Remove any timestamp suffix if present
            const cleanContent = content.toString().replace(/_\d+\.\d+$/, '');
            return {
                ...response.data,
                content: cleanContent
            };
        }

        return response.data;
    }

    // Creates a cancellable request
    _createCancellableRequest(requestFn) {
        const CancelToken = axios.CancelToken;
        const source = CancelToken.source();
        this._currentCancelTokens.push(source);

        const promise = requestFn(source.token)
            .finally(() => {
                const index = this._currentCancelTokens.indexOf(source);
                if (index > -1) {
                    this._currentCancelTokens.splice(index, 1);
                }
            });

        return promise;
    }

    // Check if error is due to request cancellation
    _isRequestCancelled(error) {
        return axios.isCancel(error);
    }

    // Log request time if debug enabled
    _logRequestTime(endpoint, startTime) {
        if (this.debug) {
            const duration = Date.now() - startTime;
            const message = `${endpoint} took ${duration}ms`;
            console.log(message);
            return message;
        }
    }

    // Track request performance
    _trackRequest(failed = false, startTime = null) {
        const endTime = Date.now();
        const duration = startTime ? endTime - startTime : 0;

        // Update metrics
        this._metrics.totalRequests++;
        if (failed) {
            this._metrics.failedRequests++;
        }
        this._metrics.totalDuration += duration;
        this._metrics.successRate = ((this._metrics.totalRequests - this._metrics.failedRequests) / this._metrics.totalRequests) * 100;

        // Add to history
        const requestInfo = {
            timestamp: new Date().toISOString(),
            duration,
            failed
        };

        this._requestHistory.unshift(requestInfo);
        if (this._requestHistory.length > this._historyLimit) {
            this._requestHistory.pop();
        }
    }

    // Get request history
    getRequestHistory() {
        return [...this._requestHistory];
    }

    // Get performance metrics
    getPerformanceMetrics() {
        const { totalRequests, failedRequests, totalDuration, successRate } = this._metrics;
        return {
            totalRequests,
            failedRequests,
            totalDuration,
            successRate
        };
    }

    // Expose constants for external use if needed
    static get DEFAULT_HOST() {
        return DEFAULT_HOST;
    }

    static get DEFAULT_PORT() {
        return DEFAULT_PORT;
    }

    static get DEFAULT_BASE_URL() {
        return DEFAULT_BASE_URL;
    }

    /**
     * Delete all cards
     * @returns {Promise<void>}
     */
    async deleteCards() {
        try {
            const cards = await this.listCards();
            await Promise.all(cards.map(card => this.deleteCard(card.hash)));
        } catch (error) {
            throw error;
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
