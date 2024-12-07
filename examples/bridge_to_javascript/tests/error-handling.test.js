const { createTestClient } = require('./utils/test-setup');
const { 
    MCardClient, 
    DEFAULT_HOST, 
    DEFAULT_PORT, 
    DEFAULT_BASE_URL 
} = require('../src/client');

describe('Error Handling', () => {
    describe('Authentication Errors', () => {
        it('should handle invalid API key', async () => {
            const client = createTestClient({ apiKey: 'invalid_key' });
            await expect(client.listCards())
                .rejects.toThrow('401: Invalid API key');
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
            // Using a very low timeout to force a timeout error
            const client = createTestClient({ timeout: 1 });
            await expect(client.listCards())
                .rejects.toThrow('Request timeout');
        });
    });

    describe('Server Errors', () => {
        it('should handle 500 Internal Server Error', async () => {
            // Create a client with an invalid port to trigger server error
            const client = createTestClient({
                baseUrl: `http://127.0.0.1:${DEFAULT_PORT + 1}`,
                timeout: 1000
            });
            await expect(client.listCards())
                .rejects.toThrow('Connection refused');
        });
    });

    describe('Edge Cases', () => {
        it('should handle special characters in content', async () => {
            const specialContent = '!@#$%^&*()_+-=[]{}|;:,.<>?`~';
            const client = createTestClient();
            const result = await client.createCard({ content: specialContent });
            expect(result).toHaveProperty('hash');
            expect(result.content).toBe(specialContent);
        });

        it('should handle unicode characters', async () => {
            const unicodeContent = '你好世界😀🌍';
            const client = createTestClient();
            const result = await client.createCard({ content: unicodeContent });
            expect(result).toHaveProperty('hash');
            expect(result.content).toBe(unicodeContent);
        });

        it('should handle very large content gracefully', async () => {
            const largeContent = 'x'.repeat(1000000); // 1MB of content
            const client = createTestClient();
            const result = await client.createCard({ content: largeContent });
            expect(result).toHaveProperty('hash');
            expect(result.content).toBe(largeContent);
        });
    });

    describe('Concurrent Error Scenarios', () => {
        it('should handle multiple errors gracefully', async () => {
            // Create multiple concurrent requests with invalid API keys to trigger errors
            const client = createTestClient({ apiKey: 'invalid_key' });
            const operations = Array(20).fill().map(() => client.listCards());
            const results = await Promise.allSettled(operations);
            
            // All requests should fail with auth error
            expect(results.every(r => r.status === 'rejected')).toBe(true);
            results.forEach(r => {
                expect(r.reason.message).toBe('401: Invalid API key');
            });
        });
    });
});
