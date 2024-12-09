const { TestEnvironment } = require('./utils/test-utils');
const { 
    MCardClient, 
    NetworkError, 
    ValidationError, 
    AuthorizationError,
    ContentValidator 
} = require('../src/client');

describe('MCard Advanced Error Handling Tests', () => {
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

    describe('Content Validation Errors', () => {
        test('should throw ValidationError for extremely long content', async () => {
            await expect(
                client.createCard(
                    'a'.repeat(2000000)
                )
            ).rejects.toThrow(ValidationError);
        });
    });

    describe('Content Type Validation', () => {
        test('should detect binary content', () => {
            const contentValidator = new ContentValidator();

            // Test base64 encoded binary content
            const base64Binary = Buffer.from('Hello, World!').toString('base64');
            expect(contentValidator.isBinary(base64Binary)).toBe(true);

            // Test text content
            expect(contentValidator.isBinary('Hello, World!')).toBe(false);
            expect(contentValidator.isBinary(42)).toBe(false);
            expect(contentValidator.isBinary(null)).toBe(false);
        });

        test('should handle different content types', () => {
            const contentValidator = new ContentValidator();

            // Test primitive types
            expect(contentValidator.stringify(42)).toBe('42');
            expect(contentValidator.stringify(true)).toBe('true');
            expect(contentValidator.stringify(null)).toBe('');

            // Test complex types
            const complexObj = { key: 'value', nested: { a: 1 } };
            expect(contentValidator.stringify(complexObj)).toBe(JSON.stringify(complexObj));
        });

        test('should handle unicode and special characters', async () => {
            const unicodeContent = '🌍 Hello, World! こんにちは';
            const card = await client.createCard(unicodeContent);
            expect(card).toHaveProperty('hash');
        });
    });

    describe('Network-Related Error Handling', () => {
        test('should handle network-related issues', async () => {
            const networkErrorClient = new MCardClient({
                baseURL: 'http://non-existent-server:9999',
                apiKey: 'dev_key_123'
            });

            await expect(networkErrorClient.createCard('Test content'))
                .rejects.toThrow(NetworkError);
        });

        test('should throw AuthorizationError for missing API key', () => {
            expect(() => new MCardClient({
                baseURL: 'http://localhost:5320'
            })).toThrow(AuthorizationError);
        });
    });
});
