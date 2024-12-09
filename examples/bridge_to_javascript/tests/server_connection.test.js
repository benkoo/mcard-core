const { TestEnvironment } = require('./utils/test-utils');
const MCardClient = require('../src/client');
const { NetworkError, ValidationError, NotFoundError, AuthorizationError } = require('../src/client');

describe('MCard Server Connection', () => {
    let testEnv;
    let client;

    beforeAll(async () => {
        testEnv = await TestEnvironment.getGlobalInstance();
        
        client = new MCardClient({
            baseURL: 'http://localhost:5320',
            apiKey: 'dev_key_123'
        });
    });

    afterAll(async () => {
        await TestEnvironment.cleanupGlobalInstance();
    });

    test('should connect to server health endpoint', async () => {
        const healthCheck = await client.healthCheck();
        expect(healthCheck).toBeTruthy();
    });

    test('should create a simple card', async () => {
        const cardData = await client.createCard('Hello, MCard!');
        expect(cardData).toHaveProperty('hash');
        expect(cardData.content).toBe('Hello, MCard!');
    });

    test('should retrieve a created card', async () => {
        const createdCard = await client.createCard('Test Retrieval');
        const retrievedCard = await client.getCard(createdCard.hash);
        
        expect(retrievedCard).toHaveProperty('content', 'Test Retrieval');
        expect(retrievedCard.hash).toBe(createdCard.hash);
    });

    test('should delete a card', async () => {
        const createdCard = await client.createCard('To be deleted');
        const deleteResult = await client.deleteCard(createdCard.hash);
        
        expect(deleteResult).toBe(true);

        // Verify card is no longer retrievable
        await expect(client.getCard(createdCard.hash)).rejects.toThrow(NotFoundError);
    });
});
