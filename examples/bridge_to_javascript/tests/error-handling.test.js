const { MCardClient, ERROR_MESSAGES } = require('../src/client');
const { TestEnvironment } = require('./utils/test-utils');

describe('MCard Client Error Handling', () => {
    let client;
    let testEnv;

    beforeAll(async () => {
        testEnv = await TestEnvironment.getGlobalInstance();
    });

    afterAll(async () => {
        await TestEnvironment.cleanupGlobalInstance();
    });

    beforeEach(async () => {
        client = new MCardClient();
        await client.deleteCards();
    });

    describe('Input Validation', () => {
        it('should reject null or undefined content', async () => {
            await expect(client.createCard()).rejects.toThrow(ERROR_MESSAGES.CONTENT_REQUIRED);
            await expect(client.createCard(null)).rejects.toThrow(ERROR_MESSAGES.CONTENT_REQUIRED);
        });

        it('should validate hash parameter', async () => {
            await expect(client.getCard()).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
            await expect(client.deleteCard()).rejects.toThrow(ERROR_MESSAGES.HASH_REQUIRED);
        });
    });

    describe('Network Errors', () => {
        it('should handle connection failures', async () => {
            const badClient = new MCardClient({
                baseURL: 'http://nonexistent.domain',
                timeout: 500
            });

            // Simulate network error by using a non-existent domain
            await expect(badClient.checkHealth())
                .rejects.toThrow(ERROR_MESSAGES.NETWORK_ERROR);
        });
    });

    describe('HTTP Status Errors', () => {
        it('should handle 404 errors', async () => {
            // Attempt to get a non-existent card
            await expect(client.getCard('nonexistent-hash'))
                .rejects.toThrow(ERROR_MESSAGES.CARD_NOT_FOUND);
        });
    });
});