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

describe('MCardClient Initialization', () => {
    describe('Client Initialization', () => {
        let originalEnv;

        beforeEach(() => {
            originalEnv = process.env.MCARD_API_KEY;
            delete process.env.MCARD_API_KEY;
        });

        afterEach(() => {
            process.env.MCARD_API_KEY = originalEnv;
        });

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
    });

    describe('API Key Validation Tests', () => {
        it('should reject whitespace-only API keys', () => {
            expect(() => {
                new MCardClient({ apiKey: '   ' });
            }).toThrow(ERROR_MESSAGES.API_KEY_REQUIRED);
        });

        it('should handle API key changes after initialization', async () => {
            const client = createTestClient();
            client.setApiKey(config.client.invalidConfig.apiKey);
            
            await expect(client.listCards())
                .rejects
                .toThrow('403: Invalid API key');
        });
    });

    describe('URL and Base Path Tests', () => {
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

        it('should handle custom ports in base URL', () => {
            const customPort = config.server.port;
            const client = new MCardClient({
                apiKey: config.server.apiKey, 
                baseUrl: `${DEFAULT_HOST}:${customPort}`
            });
            expect(client.baseUrl).toBe(`${DEFAULT_HOST}:${customPort}`);
        });
    });
});
