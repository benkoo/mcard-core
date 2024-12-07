const { 
    MCardClient, 
    DEFAULT_HOST, 
    DEFAULT_PORT, 
    DEFAULT_BASE_URL,
    ERROR_MESSAGES 
} = require('../src/client');
const { config } = require('./config/test-config');
const { createTestClient, createInvalidClient } = require('./utils/test-setup');
const nock = require('nock');

describe('MCardClient', () => {
    let client;
    let originalEnv;

    beforeEach(() => {
        originalEnv = process.env.MCARD_API_KEY;
        delete process.env.MCARD_API_KEY;
        client = createTestClient();
    });

    afterEach(() => {
        process.env.MCARD_API_KEY = originalEnv;
    });

    describe('Client Initialization', () => {
        it('should throw error when API key is missing', () => {
            expect(() => {
                new MCardClient();
            }).toThrow(ERROR_MESSAGES.API_KEY_REQUIRED);
        });

        it('should use default port when not specified', () => {
            const client = new MCardClient({ apiKey: config.server.apiKey });
            expect(client.baseUrl).toBe(DEFAULT_BASE_URL);
        });

        it('should use custom port when specified', () => {
            const customPort = config.server.port;
            const client = new MCardClient({ 
                apiKey: config.server.apiKey, 
                port: customPort 
            });
            expect(client.baseUrl).toBe(`${DEFAULT_HOST}:${customPort}`);
        });

        it('should reject whitespace-only API keys', () => {
            expect(() => {
                new MCardClient({ apiKey: '   ' });
            }).toThrow(ERROR_MESSAGES.API_KEY_REQUIRED);
        });

        it('should handle API key changes after initialization', async () => {
            client.setApiKey(config.client.invalidConfig.apiKey);
            await expect(client.listCards())
                .rejects
                .toThrow('403: Invalid API key');
        });
    });

    describe('Basic Operations', () => {
        it('should create and retrieve a card with text content', async () => {
            const content = 'Test content';
            const card = await client.createCard(content);
            expect(card).toHaveProperty('hash');
            expect(card).toHaveProperty('content');

            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toMatch(new RegExp(`^${content}`)); 
            expect(retrieved.hash).toBe(card.hash);
        });

        it('should list multiple cards', async () => {
            const cards = [];
            for (let i = 0; i < 3; i++) {
                const card = await client.createCard(`Test content ${i}`);
                cards.push(card);
            }

            const listed = await client.listCards();
            expect(Array.isArray(listed)).toBe(true);
            expect(listed.length).toBeGreaterThanOrEqual(cards.length);
        });

        it('should delete a card', async () => {
            const card = await client.createCard('Test content');
            await client.deleteCard(card.hash);
            const response = await client.getCard(card.hash);
            expect(response.detail).toBe("Card not found");
        });
    });

    describe('Content Types', () => {
        it('should handle HTML content', async () => {
            const htmlContent = '<div>Test HTML content</div>';
            const card = await client.createCard(htmlContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toMatch(new RegExp(`^${htmlContent}`)); 
        });

        it('should handle code content', async () => {
            const codeContent = 'function test() { return true; }';
            const card = await client.createCard(codeContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content.startsWith(codeContent)).toBe(true);
        });

        it('should handle large content', async () => {
            const largeContent = 'x'.repeat(1000); 
            const card = await client.createCard(largeContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toMatch(new RegExp(`^${largeContent}`)); 
        });
    });

    describe('Error Handling', () => {
        it('should handle invalid API key', async () => {
            const invalidClient = createInvalidClient();
            await expect(invalidClient.listCards())
                .rejects
                .toThrow(ERROR_MESSAGES.INVALID_API_KEY);
        });

        it('should handle non-existent card', async () => {
            const response = await client.getCard('nonexistent');
            expect(response.detail).toBe("Card not found");
        });

        it('should handle empty content', async () => {
            await expect(client.createCard(''))
                .rejects
                .toThrow(ERROR_MESSAGES.CONTENT_INVALID);
        });

        it('should handle network timeouts', async () => {
            const timeoutClient = new MCardClient({
                apiKey: config.server.apiKey,
                timeout: 1
            });
            await expect(timeoutClient.listCards())
                .rejects
                .toThrow(ERROR_MESSAGES.TIMEOUT);
        });
    });

    describe('Concurrent Operations', () => {
        it('should handle multiple concurrent card creations', async () => {
            const operations = [];
            for (let i = 0; i < 10; i++) {
                operations.push(client.createCard(`Test content ${i}`));
            }
            const results = await Promise.all(operations);
            expect(results.length).toBe(10);
            results.forEach(card => {
                expect(card).toHaveProperty('hash');
                expect(card).toHaveProperty('content');
            });
        });

        it('should handle mixed operations concurrently', async () => {
            const card1 = await client.createCard('Test content 1');
            const card2 = await client.createCard('Test content 2');

            const operations = [
                client.getCard(card1.hash),
                client.getCard(card2.hash),
                client.createCard('Test content 3'),
                client.listCards()
            ];

            const results = await Promise.all(operations);
            expect(results.length).toBe(4);
        });

        it('should maintain consistency under concurrent load', async () => {
            const cards = [];
            for (let i = 0; i < 5; i++) {
                const card = await client.createCard(`Test content ${i}`);
                cards.push(card);
            }

            const getOperations = cards.map(card => client.getCard(card.hash));
            const results = await Promise.all(getOperations);

            results.forEach((result, index) => {
                expect(result.hash).toBe(cards[index].hash);
                expect(result.content.startsWith(cards[index].content)).toBe(true);
            });
        });
    });

    describe('Performance Monitoring', () => {
        it('should track request metrics', async () => {
            const client = createTestClient();
            await client.createCard('Test content');
            const metrics = client.getMetrics();
            expect(metrics.totalRequests).toBe(1);
            expect(metrics.successfulRequests).toBe(1);
            expect(metrics.failedRequests).toBe(0);
            expect(metrics.totalDuration).toBeGreaterThan(0);
        });

        it('should reset metrics correctly', async () => {
            const client = createTestClient();
            await client.createCard('Test content');
            client.resetMetrics();
            const metrics = client.getMetrics();
            expect(metrics.totalRequests).toBe(0);
            expect(metrics.successfulRequests).toBe(0);
            expect(metrics.failedRequests).toBe(0);
            expect(metrics.totalDuration).toBe(0);
        });

        it('should handle base URL changes', () => {
            const client = createTestClient();
            const newBaseUrl = 'http://localhost:5321';
            client.baseUrl = newBaseUrl;
            expect(client.baseUrl).toBe(newBaseUrl);
        });

        it('should handle invalid base URL format', () => {
            // Test the constructor's URL formatting
            const client = new MCardClient({
                apiKey: 'test_key',
                baseUrl: 'example.com:8080'
            });
            expect(client.baseUrl).toBe('http://example.com:8080');
            
            // Test direct baseUrl setter (uses axios default behavior)
            client.baseUrl = 'another.com:8080';
            expect(client.baseUrl).toBe('another.com:8080');
        });

        it('should handle network errors without config', async () => {
            const client = createTestClient();
            const mockAxios = {
                request: jest.fn(),
                interceptors: {
                    request: { use: jest.fn() },
                    response: { 
                        use: jest.fn(),
                        handlers: []
                    }
                }
            };

            client.axiosInstance = mockAxios;
            client._addInterceptors();

            const errorHandler = mockAxios.interceptors.response.use.mock.calls[0][1];
            const error = { message: 'Network Error' }; 
            
            await expect(errorHandler(error))
                .rejects
                .toEqual(error);
        });

        it('should handle maximum retries exceeded', async () => {
            const client = createTestClient();
            const mockAxios = {
                request: jest.fn(),
                interceptors: {
                    request: { use: jest.fn() },
                    response: { 
                        use: jest.fn(),
                        handlers: []
                    }
                }
            };

            client.axiosInstance = mockAxios;
            client._addInterceptors();

            const errorHandler = mockAxios.interceptors.response.use.mock.calls[0][1];
            
            // Call the error handler with max retries exceeded
            const error = {
                config: { _retryCount: 3 }, // maxRetries is 3
                response: { status: 500 }
            };

            await expect(errorHandler(error))
                .rejects
                .toEqual(error);
        });

        it('should not retry on non-retryable status codes', async () => {
            const client = createTestClient();
            const mockAxios = {
                request: jest.fn(),
                interceptors: {
                    request: { use: jest.fn() },
                    response: { 
                        use: jest.fn(),
                        handlers: []
                    }
                }
            };

            client.axiosInstance = mockAxios;
            client._addInterceptors();

            const errorHandler = mockAxios.interceptors.response.use.mock.calls[0][1];
            
            // Call the error handler with a non-retryable status code
            const error = {
                config: { _retryCount: 0 },
                response: { status: 400 } // 400 is not in RETRY_STATUS_CODES
            };

            await expect(errorHandler(error))
                .rejects
                .toEqual(error);
        });
    });

    describe('Rate Limiting and Server Errors', () => {
        it('should handle rate limiting', async () => {
            const operations = Array(100).fill(null).map((_, i) => 
                client.createCard(`Test content ${i}`)
            );
            
            const results = await Promise.allSettled(operations);
            const errors = results.filter(r => r.status === 'rejected').map(r => r.reason);
            
            // Either we get rate limited (429) or all requests succeed
            const hasRateLimitError = errors.some(error => 
                error && error.message && error.message.includes('429')
            );
            const allSucceeded = errors.length === 0;
            
            expect(hasRateLimitError || allSucceeded).toBe(true);
        });

        it('should handle server errors gracefully', async () => {
            nock(client.baseUrl)
                .post('/cards')
                .reply(500, { error: 'Internal Server Error' });

            await expect(client.createCard('Test content'))
                .rejects
                .toThrow(ERROR_MESSAGES.SERVER_ERROR);
        });
    });

    describe('URL and Base Path', () => {
        it('should handle trailing slashes in base URL', () => {
            const client = new MCardClient({
                apiKey: config.server.apiKey, 
                baseUrl: `${DEFAULT_HOST}:${config.server.port}/`
            });
            expect(client.baseUrl).not.toMatch(/\/$/);
        });

        it('should handle missing protocol in base URL', () => {
            const client = new MCardClient({
                apiKey: config.server.apiKey, 
                baseUrl: `localhost:${config.server.port}`
            });
            expect(client.baseUrl).toBe(`${DEFAULT_HOST}:${config.server.port}`);
        });
    });
});
