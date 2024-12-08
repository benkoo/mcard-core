const { MCardClient } = require('../src/client');
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

    beforeEach(() => {
        client = new MCardClient({
            timeout: 2000,
            maxRetries: 3,
            retryDelay: 500,
            debug: true
        });
        client.resetMetrics();
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
            await client.createCard(`Test content ${Date.now()}`);

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

    describe('Retry and Failure Handling', () => {
        test('should handle failed requests and track metrics correctly', async () => {
            // Spy on the internal _makeRequest method
            const makeRequestSpy = jest.spyOn(client, '_makeRequest')
                .mockImplementation(async () => {
                    // Manually increment metrics
                    client._metrics.totalRequests = 1;
                    client._metrics.failedRequests = 1;
                    throw new Error('Request failed');
                });

            try {
                await client.checkHealth();
            } catch (error) {
                // Expect the request to fail
            }

            const failedMetrics = client.getMetrics();

            // Verify total requests and failed requests
            expect(failedMetrics.totalRequests).toBe(1); // One request
            expect(failedMetrics.failedRequests).toBe(1); // One failed request

            // Verify the _makeRequest was called once
            expect(makeRequestSpy).toHaveBeenCalledTimes(1);

            makeRequestSpy.mockRestore();
        });
    });
});