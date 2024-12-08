const axios = require('axios');
const dotenv = require('dotenv');

// Constants
const DEFAULT_HOST = 'http://localhost';
const DEFAULT_PORT = 5320;
const DEFAULT_TIMEOUT = 5000;
const DEFAULT_API_KEY = 'dev_key_123';

// Enhanced Error Classes
class MCardError extends Error {
    constructor(message, type, originalError = null, status = null) {
        super(message);
        this.name = 'MCardError';
        this.type = type;
        this.originalError = originalError;
        this.status = status;
        
        // Capture stack trace, excluding constructor call from it
        Error.captureStackTrace(this, this.constructor);
    }

    toJSON() {
        return {
            name: this.name,
            message: this.message,
            type: this.type,
            status: this.status
        };
    }
}

class NetworkError extends MCardError {
    constructor(message, originalError) {
        super(message, 'NETWORK_ERROR', originalError, 0);
        this.name = 'NetworkError';
    }
}

class ValidationError extends MCardError {
    constructor(message, originalError) {
        super(message, 'VALIDATION_ERROR', originalError, 422);
        this.name = 'ValidationError';
    }
}

class AuthorizationError extends MCardError {
    constructor(message, originalError) {
        super(message, 'AUTHORIZATION_ERROR', originalError, 403);
        this.name = 'AuthorizationError';
    }
}

class NotFoundError extends MCardError {
    constructor(message, originalError) {
        super(message, 'NOT_FOUND', originalError, 404);
        this.name = 'NotFoundError';
    }
}

// Enhanced Metrics Tracker
class MetricsTracker {
    constructor(maxHistorySize = 100) {
        this.reset();
        this.maxHistorySize = maxHistorySize;
    }

    recordRequest(success, error = null) {
        this.totalRequests++;
        
        if (success) {
            this.successfulRequests++;
        } else {
            this.failedRequests++;
            
            if (error) {
                switch (error.type) {
                    case 'VALIDATION_ERROR':
                        this.errorBreakdown.validationErrors++;
                        break;
                    case 'AUTHORIZATION_ERROR':
                        this.errorBreakdown.authorizationErrors++;
                        break;
                    case 'NOT_FOUND':
                        this.errorBreakdown.notFoundErrors++;
                        break;
                    case 'NETWORK_ERROR':
                        this.errorBreakdown.networkErrors++;
                        break;
                    case 'SERVER_ERROR':
                        this.errorBreakdown.serverErrors++;
                        break;
                    default:
                        this.errorBreakdown.unknownErrors++;
                }
            }
        }
    }

    reset() {
        this.totalRequests = 0;
        this.successfulRequests = 0;
        this.failedRequests = 0;
        this.errorBreakdown = {
            validationErrors: 0,
            authorizationErrors: 0,
            notFoundErrors: 0,
            networkErrors: 0,
            serverErrors: 0,
            unknownErrors: 0
        };
    }

    getMetrics() {
        return {
            totalRequests: this.totalRequests,
            successfulRequests: this.successfulRequests,
            failedRequests: this.failedRequests,
            errorBreakdown: this.errorBreakdown
        };
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
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [${Object.keys(Logger.LEVELS).find(key => Logger.LEVELS[key] === level)}]`;
        
        switch(level) {
            case Logger.LEVELS.DEBUG:
                console.log(prefix, ...args);
                break;
            case Logger.LEVELS.INFO:
                console.log(prefix, ...args);
                break;
            case Logger.LEVELS.WARN:
                console.warn(prefix, ...args);
                break;
            case Logger.LEVELS.ERROR:
                console.error(prefix, ...args);
                break;
        }
    }

    debug(...args) {
        if (this.level <= Logger.LEVELS.DEBUG) {
            this._log(Logger.LEVELS.DEBUG, ...args);
        }
    }

    info(...args) {
        if (this.level <= Logger.LEVELS.INFO) {
            this._log(Logger.LEVELS.INFO, ...args);
        }
    }

    warn(...args) {
        if (this.level <= Logger.LEVELS.WARN) {
            this._log(Logger.LEVELS.WARN, ...args);
        }
    }

    error(...args) {
        if (this.level <= Logger.LEVELS.ERROR) {
            this._log(Logger.LEVELS.ERROR, ...args);
        }
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
        this.metrics = null;
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

    withMetrics(maxHistorySize = 100) {
        this.metrics = new MetricsTracker(maxHistorySize);
        return this;
    }

    withContentValidators(validators) {
        this.contentValidators = validators;
        return this;
    }

    build() {
        // Create logger based on debug mode
        this.logger = new Logger(
            this.debug ? Logger.LEVELS.DEBUG : Logger.LEVELS.INFO
        );

        // If metrics not explicitly set, create default
        if (!this.metrics) {
            this.metrics = new MetricsTracker();
        }

        return {
            baseURL: this.baseUrl,
            apiKey: this.apiKey,
            timeout: this.timeout,
            debug: this.debug,
            logger: this.logger,
            metrics: this.metrics,
            contentValidators: this.contentValidators
        };
    }
}

// Enhanced Content Validator
class ContentValidator {
    static validate(content, options = {}) {
        const {
            contentValidators = [],
            maxContentLength = 10000,
            minContentLength = 1
        } = options;

        // Run custom validators first
        for (const validator of contentValidators) {
            try {
                validator(content);
            } catch (error) {
                throw new ValidationError(
                    error.message || 'Custom validation failed', 
                    'CUSTOM_VALIDATION_ERROR', 
                    error
                );
            }
        }

        // Default validation
        if (!content || content.trim().length === 0) {
            throw new ValidationError('Content cannot be empty', 'VALIDATION_ERROR');
        }

        if (content.length > maxContentLength) {
            throw new ValidationError(`Content exceeds maximum length of ${maxContentLength}`, 'VALIDATION_ERROR');
        }

        if (content.length < minContentLength) {
            throw new ValidationError(`Content is shorter than minimum length of ${minContentLength}`, 'VALIDATION_ERROR');
        }

        return true;
    }

    // Safely stringify objects, handling circular references
    static safeStringify(obj, space = 2) {
        const seen = new WeakSet();
        return JSON.stringify(obj, (key, value) => {
            if (typeof value === "object" && value !== null) {
                if (seen.has(value)) {
                    return '[Circular]';
                }
                seen.add(value);
            }
            return value;
        }, space);
    }
}

// Enhanced MCard Client
class EnhancedMCardClient {
    constructor(config = {}) {
        // Use configuration builder
        const {
            baseURL,
            apiKey,
            timeout,
            debug,
            logger,
            metrics,
            contentValidators = [] // Add support for custom content validators
        } = new MCardClientConfig()
            .withBaseUrl(config.baseURL || `${DEFAULT_HOST}:${DEFAULT_PORT}`)
            .withApiKey(config.apiKey || DEFAULT_API_KEY)
            .withTimeout(config.timeout || DEFAULT_TIMEOUT)
            .enableDebug(config.debug)
            .withMetrics()
            .withContentValidators(config.contentValidators || [])
            .build();

        this._baseURL = baseURL;
        this._apiKey = apiKey;
        this._logger = logger;
        this._metrics = metrics;
        this._contentValidators = contentValidators; // Store custom validators

        // Create axios instance with enhanced configuration
        this._axiosInstance = axios.create({
            baseURL: this._baseURL,
            timeout: timeout,
            headers: {
                'X-API-Key': this._apiKey
            }
        });

        // Add request interceptor for logging and metrics
        this._axiosInstance.interceptors.request.use(
            config => {
                config.metadata = { startTime: Date.now() };
                this._logger.debug(`Sending request to ${config.url}`, config);
                return config;
            },
            error => {
                this._logger.error('Request error', error);
                return Promise.reject(error);
            }
        );

        // Add response interceptor for logging and metrics
        this._axiosInstance.interceptors.response.use(
            response => {
                const endTime = Date.now();
                const responseTime = endTime - response.config.metadata.startTime;
                
                this._metrics.recordRequest(true);

                this._logger.debug(`Response from ${response.config.url}`, {
                    status: response.status,
                    responseTime
                });

                return response;
            },
            error => {
                const endTime = Date.now();
                const responseTime = error.config 
                    ? endTime - error.config.metadata.startTime 
                    : 0;

                let mappedError;
                if (error.response) {
                    // The request was made and the server responded with a status code
                    // that falls out of the range of 2xx
                    switch (error.response.status) {
                        case 400:
                        case 422:
                            mappedError = new ValidationError(
                                error.response.data?.error || 'Invalid request', 
                                'VALIDATION_ERROR', 
                                error, 
                                error.response.status
                            );
                            break;
                        case 401:
                        case 403:
                            mappedError = new AuthorizationError('Unauthorized', 'AUTHORIZATION_ERROR', error, error.response.status);
                            break;
                        case 404:
                            // More robust error mapping for 404
                            const errorMessage = error.response.data?.error || '';
                            if (errorMessage.toLowerCase().includes('content') || 
                                errorMessage.toLowerCase().includes('validation')) {
                                mappedError = new ValidationError('Content validation failed', 'VALIDATION_ERROR', error, error.response.status);
                            } else {
                                mappedError = new NotFoundError('Card not found', 'NOT_FOUND', error, error.response.status);
                            }
                            break;
                        case 500:
                            mappedError = new MCardError('Server error', 'SERVER_ERROR', error, error.response.status);
                            break;
                        default:
                            mappedError = new MCardError('Unexpected error', 'UNKNOWN_ERROR', error, error.response.status);
                    }
                } else if (error.request) {
                    // This means the request was made but no response was received
                    // This is typically a network connectivity issue
                    mappedError = new NetworkError('Network connectivity error', 'NETWORK_ERROR', error);
                } else {
                    // Something happened in setting up the request that triggered an Error
                    mappedError = new NetworkError('Request setup error', 'NETWORK_ERROR', error);
                }

                this._metrics.recordRequest(false, mappedError);

                this._logger.error('Request failed', mappedError);

                return Promise.reject(mappedError);
            }
        );
    }

    _validate(content) {
        // Run custom validators first
        for (const validator of this._contentValidators) {
            let validationResult;
            
            // Support both function and object-based validators
            if (typeof validator === 'function') {
                try {
                    // If it's a function, call it directly
                    validator(content);
                } catch (error) {
                    // If the function throws a ValidationError, rethrow it
                    if (error instanceof ValidationError) {
                        throw error;
                    }
                    // Otherwise, create a new ValidationError
                    throw new ValidationError(error.message || 'Custom validation failed');
                }
            } else if (validator.validate) {
                // If it's an object with a validate method
                validationResult = validator.validate(content);
                if (!validationResult.valid) {
                    throw new ValidationError(validationResult.message || 'Custom validation failed');
                }
            } else {
                throw new TypeError('Invalid validator: must be a function or have a validate method');
            }
        }

        // Default content validation
        if (!content || content.trim().length === 0) {
            throw new ValidationError('Content cannot be empty');
        }

        if (content.length > 1000) {
            throw new ValidationError('Content length exceeds maximum limit of 1000 characters');
        }

        return true;
    }

    async createCard(content, metadata = {}) {
        // Validate content before making the request
        this._validate(content);

        try {
            const response = await this._axiosInstance.post('/cards', { 
                content, 
                metadata 
            });
            return response.data;
        } catch (error) {
            throw error; // Let the interceptor handle error mapping and metrics
        }
    }

    // Add mock methods for testing scenarios
    getCard(hash) {
        return this._axiosInstance.get(`/cards/${hash}`)
            .then(response => response.data);
    }

    async deleteCard(hash) {
        if (!hash) {
            throw new ValidationError('Hash is required');
        }

        try {
            const response = await this._axiosInstance.delete(`/card/${hash}`);
            return response.data;
        } catch (error) {
            this._logger.error('Delete card failed', error);
            throw error;
        }
    }

    getMetrics() {
        return this._metrics.getMetrics();
    }

    resetMetrics() {
        this._metrics.reset();
    }
}

module.exports = {
    EnhancedMCardClient,
    MCardError,
    NetworkError,
    ValidationError,
    AuthorizationError,
    NotFoundError,
    Logger,
    ContentValidator,
    MetricsTracker
};
