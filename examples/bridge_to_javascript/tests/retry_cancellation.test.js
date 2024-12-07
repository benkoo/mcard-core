const { MCardClient, ERROR_MESSAGES } = require('../src/client');
const { TestEnvironment } = require('./utils/test-utils');
const axios = require('axios');

describe('MCard Client Retry and Cancellation', () => {
    let client;
    let testEnv;

    beforeAll(async () => {
        testEnv = await TestEnvironment.getGlobalInstance();
    });

    afterAll(async () => {
        await TestEnvironment.cleanupGlobalInstance();
    });

    beforeEach(() => {
        client = new MCardClient();
    });

    it('should handle retry exhaustion', async () => {
        const badClient = new MCardClient({
            baseURL: 'http://nonexistent.domain:12345',
            maxRetries: 2,
            retryDelay: 100,
            timeout: 500
        });

        await expect(badClient.checkHealth())
            .rejects.toThrow(ERROR_MESSAGES.RETRY_EXHAUSTED);
    });

    it('should handle empty responses', async () => {
        const response = await client.deleteCard('nonexistent');
        expect(response).toBeNull();
    });

    it('should track failed requests in metrics', async () => {
        const badClient = new MCardClient({
            baseURL: 'http://nonexistent.domain:12345',
            maxRetries: 2,
            retryDelay: 100,
            timeout: 500
        });

        try {
            await badClient.checkHealth();
        } catch (error) {
            // Expected to fail
        }

        const metrics = badClient.getMetrics();
        expect(metrics.failedRequests).toBe(1);
        expect(metrics.totalRequests).toBe(1);
        expect(metrics.retryAttempts).toBe(2);
    });

    it('should handle request cancellation', async () => {
        const slowClient = new MCardClient({
            timeout: 5000
        });
        
        const source = axios.CancelToken.source();
        const promise = slowClient.checkHealth(source.token);

        // Cancel the request
        source.cancel();
        
        await expect(promise).rejects.toThrow('cancelled');
    });
});
