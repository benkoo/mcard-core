const { MCardClient, ERROR_MESSAGES } = require('../src/client');
const { TestEnvironment } = require('./utils/test-utils');

describe('MCard Client Metrics', () => {
    let client;
    let testEnv;

    beforeAll(async () => {
        testEnv = await TestEnvironment.getGlobalInstance();
    });

    afterAll(async () => {
        await TestEnvironment.cleanupGlobalInstance();
    });

    beforeEach(async () => {
        client = new MCardClient({
            timeout: 2000,
            maxRetries: 3,
            retryDelay: 500,
            debug: true
        });
    });

    describe('Metrics Tracking', () => {
        it('should track total requests', async () => {
            const initialMetrics = client.getMetrics();
            await client.checkHealth();
            const updatedMetrics = client.getMetrics();

            expect(updatedMetrics.totalRequests).toBe(initialMetrics.totalRequests + 1);
        });

        it('should track successful and failed requests', async () => {
            const initialMetrics = client.getMetrics();

            // Successful request
            await client.checkHealth();
            const successMetrics = client.getMetrics();
            expect(successMetrics.successfulRequests).toBe(initialMetrics.successfulRequests + 1);

            // Simulate failed request
            const failedClient = new MCardClient({
                baseURL: 'http://nonexistent.domain',
                timeout: 500,
                maxRetries: 1
            });

            try {
                await failedClient.checkHealth();
            } catch (error) {
                // Expected to fail
            }

            const failedMetrics = failedClient.getMetrics();
            expect(failedMetrics.failedRequests).toBe(1);
        });

        it('should track response times', async () => {
            await client.checkHealth();
            const metrics = client.getMetrics();

            expect(metrics.averageResponseTime).toBeGreaterThanOrEqual(0);
            expect(metrics.totalResponseTime).toBeGreaterThanOrEqual(0);
        });

        it('should reset metrics correctly', () => {
            // Manually set some metrics
            const metrics = client.getMetrics();
            metrics.totalRequests = 100;
            metrics.failedRequests = 10;

            client.resetMetrics();

            const resetMetrics = client.getMetrics();
            expect(resetMetrics.totalRequests).toBe(0);
            expect(resetMetrics.failedRequests).toBe(0);
            expect(resetMetrics.successfulRequests).toBe(0);
        });

        it('should maintain request history in debug mode', async () => {
            await client.checkHealth();
            await client.createCard('Test content');

            const history = client.getRequestHistory();
            expect(history.length).toBe(2);
            
            history.forEach(entry => {
                expect(entry).toHaveProperty('timestamp');
                expect(entry).toHaveProperty('method');
                expect(entry).toHaveProperty('url');
                expect(entry).toHaveProperty('duration');
                expect(entry).toHaveProperty('success');
                expect(entry).toHaveProperty('status');
            });
        });
    });
});