const { createTestClient } = require('./utils/test-setup');
const { 
    MCardClient, 
    DEFAULT_HOST, 
    DEFAULT_PORT, 
    DEFAULT_BASE_URL 
} = require('../src/client');
const nock = require('nock');

describe('Error Handling', () => {
    beforeEach(() => {
        nock.cleanAll();
    });

    afterAll(() => {
        nock.restore();
    });

    describe('Authentication Errors', () => {
        it('should handle invalid API key', async () => {
            const scope = nock(DEFAULT_BASE_URL)
                .get('/cards')
                .reply(401, { error: 'Invalid API key' });

            const client = createTestClient({ apiKey: 'invalid_key' });
            await expect(client.listCards())
                .rejects.toThrow('401: Invalid API key');
            
            scope.done();
        });

        it('should handle missing API key', () => {
            expect(() => new MCardClient({}))
                .toThrow('API key is required');
        });
    });

    describe('Network Errors', () => {
        it('should handle connection refused', async () => {
            const client = createTestClient({
                baseUrl: `${DEFAULT_HOST}:1`,
                timeout: 100
            });
            await expect(client.listCards())
                .rejects.toThrow('Connection refused');
        });

        it('should handle timeout', async () => {
            const scope = nock(DEFAULT_BASE_URL)
                .get('/cards')
                .delayConnection(1000)
                .reply(200);

            const client = createTestClient({ timeout: 100 });
            await expect(client.listCards())
                .rejects.toThrow('Request timeout');
            
            scope.done();
        });
    });

    describe('Server Errors', () => {
        it('should handle 500 Internal Server Error', async () => {
            const scope = nock(DEFAULT_BASE_URL)
                .get('/cards')
                .reply(500, { error: 'Internal server error' });

            const client = createTestClient();
            await expect(client.listCards())
                .rejects.toThrow('500: Server error');
            
            scope.done();
        });
    });

    describe('Edge Cases', () => {
        it('should handle special characters in content', async () => {
            const specialContent = '!@#$%^&*()_+-=[]{}|;:,.<>?`~';
            const scope = nock(DEFAULT_BASE_URL)
                .post('/cards', { content: specialContent })
                .reply(200, { hash: 'test_hash', content: specialContent });

            const client = createTestClient();
            await expect(client.createCard({ content: specialContent }))
                .resolves.toHaveProperty('hash');
            
            scope.done();
        });

        it('should handle unicode characters', async () => {
            const unicodeContent = '你好世界😀🌍';
            const scope = nock(DEFAULT_BASE_URL)
                .post('/cards', { content: unicodeContent })
                .reply(200, { hash: 'test_hash', content: unicodeContent });

            const client = createTestClient();
            await expect(client.createCard({ content: unicodeContent }))
                .resolves.toHaveProperty('hash');
            
            scope.done();
        });

        it('should handle very large content gracefully', async () => {
            const largeContent = 'x'.repeat(1000000); // 1MB of content
            const scope = nock(DEFAULT_BASE_URL)
                .post('/cards', { content: largeContent })
                .reply(200, { hash: 'test_hash', content: largeContent });

            const client = createTestClient();
            await expect(client.createCard({ content: largeContent }))
                .resolves.toHaveProperty('hash');
            
            scope.done();
        });
    });

    describe('Concurrent Error Scenarios', () => {
        it('should handle multiple errors gracefully', async () => {
            const scope = nock(DEFAULT_BASE_URL)
                .get('/cards')
                .times(5)
                .reply(429, { error: 'Rate limit exceeded' });

            const client = createTestClient();
            const operations = Array(5).fill().map(() => client.listCards());
            const results = await Promise.allSettled(operations);
            
            expect(results.every(r => r.status === 'rejected')).toBe(true);
            results.forEach(r => {
                expect(r.reason.message).toBe('429: Rate limit exceeded');
            });
            
            scope.done();
        });
    });
});
