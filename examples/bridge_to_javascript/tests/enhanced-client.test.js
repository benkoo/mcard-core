const { 
    EnhancedMCardClient, 
    MCardError,
    NetworkError,
    ValidationError,
    AuthorizationError,
    NotFoundError,
    Logger
} = require('../src/enhanced-client');
const axios = require('axios');
const MockAdapter = require('axios-mock-adapter');

const defaultConfig = {
    apiKey: 'test-api-key',
    baseURL: 'http://localhost:5320',
    timeout: 5000,
    debug: false
};

describe('Enhanced MCard Client', () => {
    let client;
    let mock;

    beforeEach(() => {
        // Create a new client before each test
        client = new EnhancedMCardClient({
            baseURL: 'http://localhost:5320',
            debug: false
        });

        // Create a new mock adapter for axios
        mock = new MockAdapter(client._axiosInstance);
    });

    afterEach(() => {
        // Reset the mock adapter after each test
        if (mock) {
            mock.reset();
        }
    });

    // Error Handling Tests
    describe('Error Handling', () => {
        test('should throw ValidationError for empty content', async () => {
            await expect(client.createCard('')).rejects.toThrow(ValidationError);
        });

        test('should throw ValidationError for extremely long content', async () => {
            const longContent = 'a'.repeat(50000);
            await expect(client.createCard(longContent)).rejects.toThrow(ValidationError);
        });

        test('should throw NotFoundError for non-existent card', async () => {
            mock.onGet('/card/nonexistent-hash').reply(404);

            await expect(client.getCard('nonexistent-hash')).rejects.toThrow(NotFoundError);
        });

        test('should throw AuthorizationError for invalid API key', async () => {
            mock.onPost('/cards').reply(403);

            await expect(client.createCard('test content')).rejects.toThrow(AuthorizationError);
        });

        test('should throw NetworkError for network connectivity issues', async () => {
            mock.onPost('/cards').networkError();

            await expect(client.createCard('test content')).rejects.toThrow(NetworkError);
        });

        test('should handle unexpected server errors', async () => {
            mock.onPost('/cards').reply(500);

            await expect(client.createCard('test content')).rejects.toThrow(MCardError);
        });
    });

    // Content Validation Tests
    describe('Content Validation', () => {
        test('should validate content length', async () => {
            const longContent = 'a'.repeat(20000);
            await expect(client.createCard(longContent)).rejects.toThrow(ValidationError);
        });

        test('should allow custom content validators', async () => {
            // Setup mock for successful card creation
            mock.onPost('/cards').reply(201, { hash: 'test-hash' });

            const customClient = new EnhancedMCardClient({
                baseURL: 'http://localhost:5320',
                debug: false,
                contentValidators: [
                    (content) => {
                        if (content.includes('invalid')) {
                            throw new ValidationError('Custom validation failed', 'CUSTOM_VALIDATION_ERROR');
                        }
                    }
                ]
            });

            const customMock = new MockAdapter(customClient._axiosInstance);
            customMock.onPost('/cards').reply(201, { hash: 'test-hash' });

            await expect(customClient.createCard('valid content')).resolves.toBeDefined();
            await expect(customClient.createCard('invalid content')).rejects.toThrow(ValidationError);
        });

        test('should validate content with special characters', async () => {
            const specialContent = '!@#$%^&*()_+{}:"<>?';
            mock.onPost('/cards').reply(201, { hash: 'special-hash' });

            const result = await client.createCard(specialContent);
            expect(result).toHaveProperty('hash', 'special-hash');
        });
    });

    // Metrics Tracking Tests
    describe('Metrics Tracking', () => {
        test('should track successful requests', async () => {
            mock.onPost('/cards').reply(201, { hash: 'test-hash' });
            
            await client.createCard('test content');
            
            const metrics = client.getMetrics();
            expect(metrics.totalRequests).toBe(1);
            expect(metrics.successfulRequests).toBe(1);
            expect(metrics.failedRequests).toBe(0);
        });

        test('should track failed requests', async () => {
            mock.onPost('/cards').reply(422, { error: 'Validation error' });

            await expect(client.createCard('test')).rejects.toThrow(ValidationError);

            const metrics = client.getMetrics();
            expect(metrics.totalRequests).toBe(1);
            expect(metrics.successfulRequests).toBe(0);
            expect(metrics.failedRequests).toBe(1);
            expect(metrics.errorBreakdown.validationErrors).toBe(1);
        });

        test('should track multiple requests', async () => {
            const mockReplies = [
                [201, { hash: 'test-hash-1' }],
                [201, { hash: 'test-hash-2' }],
                [500, { error: 'Server error' }]
            ];

            mock.onPost('/cards').reply(config => {
                const [status, data] = mockReplies.shift();
                return [status, data];
            });

            await client.createCard('test content 1');
            await client.createCard('test content 2');
            
            await expect(client.createCard('test content 3')).rejects.toThrow(MCardError);
            
            const metrics = client.getMetrics();
            expect(metrics.totalRequests).toBe(3);
            expect(metrics.successfulRequests).toBe(2);
            expect(metrics.failedRequests).toBe(1);
            expect(metrics.errorBreakdown.serverErrors).toBe(1);
        });

        test('should reset metrics', async () => {
            mock.onPost('/cards').reply(201, { hash: 'test-hash' });
            
            await client.createCard('test content');
            
            const metricsBefore = client.getMetrics();
            expect(metricsBefore.totalRequests).toBe(1);

            client.resetMetrics();

            const metricsAfter = client.getMetrics();
            expect(metricsAfter.totalRequests).toBe(0);
        });
    });

    // Logging Tests
    describe('Logging', () => {
        let originalConsoleLog;
        let originalConsoleError;

        beforeEach(() => {
            // Save original console methods
            originalConsoleLog = console.log;
            originalConsoleError = console.error;

            // Replace console methods with spies
            console.log = jest.fn();
            console.error = jest.fn();
        });

        afterEach(() => {
            // Restore original console methods
            console.log = originalConsoleLog;
            console.error = originalConsoleError;
        });

        test('should log debug information when debug is enabled', async () => {
            const debugClient = new EnhancedMCardClient({
                baseURL: 'http://localhost:5320',
                debug: true
            });

            const mockAxios = new MockAdapter(debugClient._axiosInstance);
            mockAxios.onPost('/cards').reply(201, { hash: 'test-hash' });
            
            await debugClient.createCard('test content');

            // Check that debug logs were called
            expect(console.log).toHaveBeenCalled();
        });

        test('should not log debug information when debug is disabled', async () => {
            const quietClient = new EnhancedMCardClient({
                baseURL: 'http://localhost:5320',
                debug: false
            });

            const mockAxios = new MockAdapter(quietClient._axiosInstance);
            mockAxios.onPost('/cards').reply(201, { hash: 'test-hash' });
            
            await quietClient.createCard('test content');

            // Check that no debug logs were called
            expect(console.log).not.toHaveBeenCalled();
        });
    });

    // Configuration Tests
    describe('Client Configuration', () => {
        test('should allow custom base URL', () => {
            const customClient = new EnhancedMCardClient({
                baseURL: 'http://custom-url:5321'
            });

            expect(client._baseURL).toBe('http://localhost:5320');
            expect(customClient._baseURL).toBe('http://custom-url:5321');
        });

        test('should use default configuration when no options provided', () => {
            const defaultClient = new EnhancedMCardClient();
            
            expect(defaultClient._baseURL).toBe('http://localhost:5320');
            expect(defaultClient._apiKey).toBe('dev_key_123');
        });

        test('should allow custom timeout configuration', () => {
            const customClient = new EnhancedMCardClient({
                timeout: 10000
            });

            expect(customClient._axiosInstance.defaults.timeout).toBe(10000);
        });
    });

    // Card Operations Tests
    describe('Card Operations', () => {
        test('should create a card successfully', async () => {
            const mockResponse = { hash: 'test-hash', content: 'test content' };
            mock.onPost('/cards').reply(201, mockResponse);

            const result = await client.createCard('test content');
            
            expect(result).toEqual(mockResponse);
        });

        test('should get a card successfully', async () => {
            const mockResponse = { hash: 'test-hash', content: 'test content' };
            mock.onGet('/cards/test-hash').reply(200, mockResponse);

            const result = await client.getCard('test-hash');
            
            expect(result.hash).toBe(mockResponse.hash);
            expect(result.content).toBe(mockResponse.content);
        });

        test('should delete a card successfully', async () => {
            const mockResponse = { message: 'Card deleted' };
            mock.onDelete('/card/test-hash').reply(200, mockResponse);

            const result = await client.deleteCard('test-hash');
            
            expect(result).toEqual(mockResponse);
        });

        test('should create a card with metadata', async () => {
            const mockResponse = { 
                hash: 'metadata-hash', 
                content: 'test content', 
                metadata: { tags: ['important'] } 
            };
            mock.onPost('/cards').reply(201, mockResponse);

            const result = await client.createCard('test content', { tags: ['important'] });
            
            expect(result).toEqual(mockResponse);
        });
    });
});
