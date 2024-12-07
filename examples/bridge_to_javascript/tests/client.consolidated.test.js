const { MCardClient, DEFAULT_API_KEY, DEFAULT_BASE_URL, DEFAULT_TIMEOUT, ERROR_MESSAGES } = require('../src/client');
const { TestEnvironment } = require('./utils/test-utils');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

describe('MCard Client', () => {
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
            apiKey: DEFAULT_API_KEY,
            baseUrl: DEFAULT_BASE_URL,
            timeout: DEFAULT_TIMEOUT
        });
    });

    describe('Basic Operations', () => {
        it('should create, retrieve, and delete a card', async () => {
            // Create a card with unique content
            const content = { 
                text: 'Test content', 
                number: 42,
                timestamp: new Date().toISOString()
            };
            const createResponse = await client.createCard({ content: JSON.stringify(content) });
            expect(createResponse).toBeDefined();
            expect(createResponse.hash).toBeDefined();
            
            // Retrieve the card
            const retrievedCard = await client.getCard(createResponse.hash);
            expect(retrievedCard).toBeDefined();
            expect(JSON.parse(retrievedCard.content)).toEqual(content);
            
            // Delete the card
            await client.deleteCard(createResponse.hash);
            
            // Verify deletion
            await expect(client.getCard(createResponse.hash)).rejects.toThrow();
        });

        it('should handle text content properly', async () => {
            const textContent = `Simple text content ${new Date().toISOString()}`;
            const response = await client.createCard(textContent);
            expect(response.hash).toBeDefined();
            
            const retrieved = await client.getCard(response.hash);
            expect(retrieved.content).toBe(textContent);
            
            await client.deleteCard(response.hash);
        });

        it('should handle structured content properly', async () => {
            const structuredContent = {
                title: 'Test Card',
                items: [1, 2, 3],
                metadata: {
                    author: 'Test User',
                    timestamp: new Date().toISOString()
                }
            };
            
            const response = await client.createCard({ content: JSON.stringify(structuredContent) });
            expect(response.hash).toBeDefined();
            
            const retrieved = await client.getCard(response.hash);
            expect(JSON.parse(retrieved.content)).toEqual(structuredContent);
            
            await client.deleteCard(response.hash);
        });
    });

    describe('Error Handling', () => {
        it('should handle invalid content gracefully', async () => {
            await expect(client.createCard()).rejects.toThrow(ERROR_MESSAGES.CONTENT_INVALID);
            await expect(client.createCard('')).rejects.toThrow(ERROR_MESSAGES.CONTENT_INVALID);
            await expect(client.createCard(null)).rejects.toThrow(ERROR_MESSAGES.CONTENT_INVALID);
            await expect(client.createCard({ content: null })).rejects.toThrow(ERROR_MESSAGES.CONTENT_INVALID);
            await expect(client.createCard({ content: '' })).rejects.toThrow(ERROR_MESSAGES.CONTENT_INVALID);
        });

        it('should handle non-existent card access', async () => {
            const nonexistentHash = 'nonexistenthash123';
            await expect(client.getCard(nonexistentHash)).rejects.toThrow(ERROR_MESSAGES.CARD_NOT_FOUND);
            const response = await client.deleteCard(nonexistentHash);
            expect(response).toBeNull();
        });

        it('should handle missing hash parameter', async () => {
            await expect(client.getCard()).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
            await expect(client.getCard('')).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
            await expect(client.getCard(null)).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
            await expect(client.deleteCard()).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
            await expect(client.deleteCard('')).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
            await expect(client.deleteCard(null)).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
        });

        it('should handle retry exhaustion', async () => {
            const badClient = new MCardClient({
                baseURL: 'http://nonexistent.domain',
                timeout: 1000,
                maxRetries: 2,
                retryDelay: 100
            });
            await expect(badClient.checkHealth()).rejects.toThrow(ERROR_MESSAGES.RETRY_EXHAUSTED);
        });

        it('should handle other HTTP errors', async () => {
            // Create a client with an invalid API key to trigger a 403 error
            const badClient = new MCardClient({
                apiKey: 'invalid_key',
                timeout: 1000
            });
            await expect(badClient.checkHealth()).rejects.toThrow('403: Invalid API key');
        });

        it('should handle other errors in deleteCard', async () => {
            // Create a client with an invalid API key to trigger a 403 error
            const badClient = new MCardClient({
                apiKey: 'invalid_key',
                timeout: 1000
            });
            await expect(badClient.deleteCard('hash123')).rejects.toThrow('403: Invalid API key');
        });

        it('should handle errors with no response data', async () => {
            const badClient = new MCardClient({
                apiKey: 'invalid_key',
                baseURL: 'http://localhost:1234', // Use a port that's not in use
                timeout: 100
            });
            await expect(badClient.checkHealth()).rejects.toThrow(ERROR_MESSAGES.NETWORK_ERROR);
        });

        it('should handle errors with no response status', async () => {
            const badClient = new MCardClient({
                baseURL: 'http://nonexistent.domain.local',
                timeout: 100
            });
            await expect(badClient.checkHealth()).rejects.toThrow(ERROR_MESSAGES.RETRY_EXHAUSTED);
        });
    });

    describe('Search and List Operations', () => {
        let createdCards = [];

        beforeEach(async () => {
            // Create test cards with unique content
            const timestamp = new Date().toISOString();
            const cards = [
                { content: `First test card with unique content ${timestamp}-1` },
                { content: `Second test card with similar content ${timestamp}-2` },
                { content: `Third test card with similar content ${timestamp}-3` }
            ];
            
            for (const card of cards) {
                const response = await client.createCard(card);
                createdCards.push(response);
            }
        });

        afterEach(async () => {
            // Cleanup created cards
            for (const card of createdCards) {
                try {
                    await client.deleteCard(card.hash);
                } catch (error) {
                    // Ignore errors during cleanup
                }
            }
            createdCards = [];
        });

        it('should list all cards with pagination', async () => {
            const result = await client.listCards({ page: 1, pageSize: 10 });
            expect(result.items).toBeDefined();
            expect(result.items.length).toBeGreaterThanOrEqual(3);
            expect(result.total).toBeGreaterThanOrEqual(3);
            expect(result.page).toBe(1);
            expect(result.page_size).toBe(10);
            expect(result.total_pages).toBeDefined();
            expect(result.has_next).toBeDefined();
            expect(result.has_previous).toBeDefined();
        });
    });

    describe('Client Configuration', () => {
        it('should initialize with custom configuration', () => {
            const customConfig = {
                apiKey: 'custom_key',
                baseURL: 'http://custom.domain:8080',
                timeout: 10000,
                debug: true,
                headers: { 'Custom-Header': 'value' }
            };
            const customClient = new MCardClient(customConfig);
            
            expect(customClient.apiKey).toBe(customConfig.apiKey);
            expect(customClient.debug).toBe(true);
            expect(customClient.axiosInstance.defaults.baseURL).toBe(customConfig.baseURL);
            expect(customClient.axiosInstance.defaults.timeout).toBe(customConfig.timeout);
            expect(customClient.axiosInstance.defaults.headers['Custom-Header']).toBe('value');
        });

        it('should normalize base URLs correctly', () => {
            const testCases = [
                { input: 'localhost:5000', expected: 'http://localhost:5000' },
                { input: 'https://api.example.com/', expected: 'https://api.example.com' },
                { input: 'http://test.com', expected: 'http://test.com' }
            ];

            testCases.forEach(({ input, expected }) => {
                const client = new MCardClient({ baseURL: input });
                expect(client.axiosInstance.defaults.baseURL).toBe(expected);
            });
        });
    });

    describe('Error Handling and Retries', () => {
        it('should handle network errors', async () => {
            const badClient = new MCardClient({
                baseURL: 'http://nonexistent.domain',
                timeout: 1000,
                maxRetries: 2,
                retryDelay: 100
            });

            await expect(badClient.checkHealth())
                .rejects
                .toThrow(ERROR_MESSAGES.RETRY_EXHAUSTED);
        });

        it('should track metrics during errors', async () => {
            const badClient = new MCardClient({
                baseURL: 'http://nonexistent.domain',
                timeout: 1000,
                maxRetries: 1,
                retryDelay: 100
            });

            try {
                await badClient.checkHealth();
            } catch (error) {
                const metrics = badClient.getMetrics();
                expect(metrics.failedRequests).toBe(1);
                expect(metrics.retryAttempts).toBeGreaterThan(0);
            }
        });
    });

    describe('Metrics and Monitoring', () => {
        it('should track successful requests', async () => {
            const startMetrics = client.getMetrics();
            await client.checkHealth();
            const endMetrics = client.getMetrics();
            expect(endMetrics.totalRequests).toBe(startMetrics.totalRequests + 1);
            expect(endMetrics.successfulRequests).toBe(startMetrics.successfulRequests + 1);
            expect(endMetrics.failedRequests).toBe(startMetrics.failedRequests);
            expect(endMetrics.averageResponseTime).toBeGreaterThan(0);
        });

        it('should reset metrics correctly', async () => {
            await client.checkHealth();
            client.resetMetrics();
            const metrics = client.getMetrics();
            expect(metrics.totalRequests).toBe(0);
            expect(metrics.successfulRequests).toBe(0);
            expect(metrics.failedRequests).toBe(0);
            expect(metrics.averageResponseTime).toBe(0);
        });

        it('should maintain request history', async () => {
            client.resetMetrics();
            await client.checkHealth();
            const history = client.getRequestHistory();
            expect(history.length).toBeGreaterThan(0);
            expect(history[0].method).toBe('GET');
            expect(history[0].url).toBe('/health');
            expect(history[0].duration).toBeGreaterThan(0);
            expect(history[0].success).toBe(true);
        });

        it('should handle request history limits', async () => {
            const maxHistorySize = 5;
            const testClient = new MCardClient({
                maxHistorySize
            });

            // Make more requests than the history size
            for (let i = 0; i < maxHistorySize + 2; i++) {
                await testClient.checkHealth();
            }

            const history = testClient.getRequestHistory();
            expect(history.length).toBe(maxHistorySize);
        });
    });

    describe('Input Validation', () => {
        it('should validate pagination parameters', async () => {
            await expect(client.listCards({ page: 0 }))
                .rejects.toThrow(ERROR_MESSAGES.INVALID_PAGE);
            
            await expect(client.listCards({ page: 1, pageSize: 0 }))
                .rejects.toThrow(ERROR_MESSAGES.INVALID_PAGE_SIZE);
            
            await expect(client.listCards({ page: 1, pageSize: 101 }))
                .rejects.toThrow(ERROR_MESSAGES.INVALID_PAGE_SIZE);
        });

        it('should validate card parameters', async () => {
            await expect(client.getCard())
                .rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
            
            await expect(client.deleteCard())
                .rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
        });
    });

    describe('Metrics and History', () => {
        it('should track request history with debug mode', async () => {
            const debugClient = new MCardClient({
                debug: true
            });

            // Make some requests
            await debugClient.checkHealth();
            await debugClient.checkHealth();
            
            const history = debugClient.getRequestHistory();
            expect(history.length).toBe(2);
            expect(history[0].method).toBe('GET');
            expect(history[0].url).toBe('/health');
            expect(history[0].duration).toBeGreaterThan(0);
            expect(history[0].success).toBe(true);
        });

        it('should handle empty responses', async () => {
            const response = await client.deleteCard('nonexistent');
            expect(response).toBeNull();
        });

        it('should track failed requests in metrics', async () => {
            const badClient = new MCardClient({
                baseURL: 'http://nonexistent.domain',
                maxRetries: 0
            });

            const startMetrics = badClient.getMetrics();
            try {
                await badClient.checkHealth();
            } catch (error) {
                const endMetrics = badClient.getMetrics();
                expect(endMetrics.failedRequests).toBe(startMetrics.failedRequests + 1);
                expect(endMetrics.totalRequests).toBe(startMetrics.totalRequests + 1);
                expect(endMetrics.successfulRequests).toBe(startMetrics.successfulRequests);
            }
        });
    });

    describe('Card Management', () => {
        beforeEach(async () => {
            // Clean up any existing cards
            await client.deleteCards();
            // Wait a bit to ensure server has processed the deletions
            await new Promise(resolve => setTimeout(resolve, 200));
        });

        it('should get all cards with pagination', async () => {
            const timestamp = Date.now();

            // Clean up any existing cards first
            await client.deleteCards();
            await new Promise(resolve => setTimeout(resolve, 200));

            // Create test cards
            const card1 = await client.createCard(`Test card 1 ${timestamp}`);
            const card2 = await client.createCard(`Test card 2 ${timestamp}`);
            const card3 = await client.createCard(`Test card 3 ${timestamp}`);

            // Wait longer to ensure server has processed all creations
            await new Promise(resolve => setTimeout(resolve, 500));

            const allCards = await client.getAllCards();
            expect(allCards.length).toBeGreaterThanOrEqual(3);

            // Cleanup
            await client.deleteCard(card1.hash);
            await client.deleteCard(card2.hash);
            await client.deleteCard(card3.hash);
            await new Promise(resolve => setTimeout(resolve, 200));
        });

        it('should handle empty response in getAllCards', async () => {
            // First delete all cards
            await client.deleteCards();
            // Wait a bit to ensure server has processed the deletions
            await new Promise(resolve => setTimeout(resolve, 200));

            const allCards = await client.getAllCards();
            expect(allCards).toHaveLength(0);
        });

        it('should delete all cards', async () => {
            // Create multiple cards with unique content
            const timestamp = Date.now();
            await client.createCard(`Test card 1 ${timestamp}`);
            await client.createCard(`Test card 2 ${timestamp}`);

            // Wait a bit to ensure server has processed the creations
            await new Promise(resolve => setTimeout(resolve, 200));

            await client.deleteCards();
            // Wait a bit to ensure server has processed the deletions
            await new Promise(resolve => setTimeout(resolve, 200));

            const remainingCards = await client.getAllCards();
            expect(remainingCards).toHaveLength(0);
        });

        it('should handle errors in deleteCards', async () => {
            // Create a client with an invalid API key to trigger errors
            const badClient = new MCardClient({
                apiKey: 'invalid_key',
                timeout: 1000
            });

            await expect(badClient.deleteCards()).rejects.toThrow('403: Invalid API key');
        });
    });

    describe('URL Normalization', () => {
        it('should normalize URLs correctly', () => {
            const client = new MCardClient();
            expect(client._normalizeBaseURL('example.com')).toBe('http://example.com');
            expect(client._normalizeBaseURL('http://example.com/')).toBe('http://example.com');
            expect(client._normalizeBaseURL('https://example.com')).toBe('https://example.com');
            expect(client._normalizeBaseURL('')).toBe(DEFAULT_BASE_URL);
            expect(client._normalizeBaseURL(null)).toBe(DEFAULT_BASE_URL);
        });
    });
});
