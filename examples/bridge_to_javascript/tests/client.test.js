const { 
    MCardClient, 
    MCardError,
    NetworkError,
    ValidationError,
    AuthorizationError,
    NotFoundError,
    Logger,
    ContentValidator,
    MCardClientConfig
} = require('../src/client');

const { spawn } = require('child_process');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

// Server management utility
class TestServerManager {
    static serverProcess = null;

    static async startServer() {
        // Kill any existing server process
        await this.stopServer();

        console.log('Starting server...');
        const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
        
        this.serverProcess = spawn(pythonPath, ['src/server.py'], {
            cwd: process.cwd(),
            stdio: 'pipe',
            detached: true
        });

        // Log server output
        this.serverProcess.stdout.on('data', (data) => {
            console.log(`Server stdout: ${data}`);
        });

        this.serverProcess.stderr.on('data', (data) => {
            console.error(`Server stderr: ${data}`);
        });

        // Wait for server to start
        await new Promise(resolve => setTimeout(resolve, 3000));
    }

    static async stopServer() {
        if (this.serverProcess) {
            try {
                // Try to shutdown gracefully
                await axios.post('http://localhost:5320/shutdown', null, {
                    headers: { 'X-API-Key': 'dev_key_123' },
                    timeout: 2000
                }).catch(() => {});

                // Kill the process
                process.kill(-this.serverProcess.pid);
            } catch (error) {
                console.warn('Error stopping server:', error);
            }
            this.serverProcess = null;
        }
    }
}

// Binary content generation utilities
function generateBinaryContent(type) {
    switch(type) {
        case 'image':
            // Small PNG header
            return Buffer.from([
                137, 80, 78, 71, 13, 10, 26, 10,  // PNG signature
                0, 0, 0, 13,  // Length of IHDR chunk
                73, 72, 68, 82,  // IHDR chunk type
                0, 0, 0, 1, 0, 0, 0, 1,  // Width and height (1x1 pixel)
                8, 6, 0, 0, 0, 31, 253, 115, 115  // Other IHDR data
            ]);
        case 'pdf':
            // Minimal PDF header
            return Buffer.from('%PDF-1.5\n1 0 obj\n<</Type/Catalog>>\nendobj\ntrailer\n<</Root 1 0 R>>');
        case 'audio':
            // Minimal WAV header
            return Buffer.from([
                82, 73, 70, 70,  // "RIFF"
                36, 0, 0, 0,     // File size (36 bytes)
                87, 65, 86, 69,  // "WAVE"
                102, 109, 116, 32 // "fmt "
            ]);
        case 'compressed':
            // Minimal ZIP header
            return Buffer.from([
                80, 75, 3, 4,    // ZIP file signature
                20, 0,           // Version needed to extract
                0, 0,            // General purpose bit flag
                0, 0,            // Compression method
                0, 0, 0, 0,      // Last mod file time and date
                0, 0, 0, 0,      // CRC-32
                0, 0, 0, 0,      // Compressed size
                0, 0, 0, 0       // Uncompressed size
            ]);
        default:
            throw new Error(`Unsupported binary content type: ${type}`);
    }
}

// Complex content generation
function generateComplexContent() {
    return [
        {
            nested: {
                array: [1, 2, 3],
                object: { key: 'value' },
                date: new Date('2024-12-09T02:52:50+08:00').toISOString()
            },
            specialChars: '!@#$%^&*()_+{}:"<>?',
            unicodeText: 'こんにちは世界 🌍 Здравствуй мир'
        }
    ];
}

describe('MCard Client', () => {
    let client;

    // Setup before all tests
    beforeAll(async () => {
        await TestServerManager.startServer();
        
        client = new MCardClient({
            baseURL: 'http://localhost:5320',
            apiKey: 'dev_key_123',
            timeout: 5000,
            debug: true
        });
    }, 10000);  // Increased timeout for server startup

    // Cleanup after all tests
    afterAll(async () => {
        await TestServerManager.stopServer();
    }, 10000);

    beforeEach(() => {
        client = new MCardClient({
            baseURL: 'http://localhost:5320',
            apiKey: 'dev_key_123',
            timeout: 2000,
            debug: true
        });
    });

    describe('Error Handling', () => {
        test('should throw ValidationError for empty content', async () => {
            await expect(client.createCard('')).rejects.toThrow(ValidationError);
            await expect(client.createCard('   ')).rejects.toThrow(ValidationError);
        });

        test('should throw ValidationError for extremely long content', async () => {
            const longContent = 'a'.repeat(1050000); // Slightly over the max length
            try {
                await client.createCard(longContent);
                // If we get here, the test should fail
                fail('Expected ValidationError to be thrown');
            } catch (error) {
                console.log('Caught error:', error);
                expect(error).toBeInstanceOf(ValidationError);
                expect(error.message).toContain('exceeds maximum length');
            }
        });
    });

    describe('Content Validation', () => {
        test('should validate content length', async () => {
            const content = 'Hello, World!';
            const card = await client.createCard(content);
            expect(card.content).toBe(content);
        });

        test('should allow creating card with special characters', async () => {
            const content = '!@#$%^&*()_+{}:"<>?';
            const card = await client.createCard(content);
            expect(card.content).toBe(content);
        });
    });

    describe('Advanced Content Validation', () => {
        test('should handle object content validation', async () => {
            const content = { key: 'value', nested: { a: 1 } };
            const card = await client.createCard(content);
            expect(card.content).toEqual(JSON.stringify(content));
        });
    });

    describe('Logging', () => {
        test('should log debug information when debug is enabled', () => {
            const mockLogger = {
                debug: jest.fn(),
                info: jest.fn(),
                warn: jest.fn(),
                error: jest.fn()
            };

            const debugClient = new MCardClient({ 
                debug: true, 
                logger: mockLogger 
            });

            debugClient._log('debug', 'Test debug message');
            expect(mockLogger.debug).toHaveBeenCalledWith('Test debug message');
        });

        test('should log at different levels', () => {
            const mockLogger = {
                debug: jest.fn(),
                info: jest.fn(),
                warn: jest.fn(),
                error: jest.fn()
            };

            const client = new MCardClient({ 
                debug: true, 
                logger: mockLogger 
            });

            client._log('debug', 'Debug');
            client._log('info', 'Info');
            client._log('warn', 'Warn');
            client._log('error', 'Error');

            expect(mockLogger.debug).toHaveBeenCalledWith('Debug');
            expect(mockLogger.info).toHaveBeenCalledWith('Info');
            expect(mockLogger.warn).toHaveBeenCalledWith('Warn');
            expect(mockLogger.error).toHaveBeenCalledWith('Error');
        });

        test('should respect log level', () => {
            const logger = new Logger(Logger.LEVELS.ERROR);
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
            const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
            const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

            logger.debug('Debug message');
            logger.info('Info message');
            logger.warn('Warning message');
            logger.error('Error message');

            expect(consoleSpy).not.toHaveBeenCalled();
            expect(consoleWarnSpy).not.toHaveBeenCalled();
            expect(consoleErrorSpy).toHaveBeenCalled();

            consoleSpy.mockRestore();
            consoleWarnSpy.mockRestore();
            consoleErrorSpy.mockRestore();
        });
    });

    describe('Advanced Error Handling', () => {
        test('should throw specific error types', async () => {
            // Simulate a non-existent hash scenario
            const nonExistentHash = 'non_existent_hash';
            await expect(client.getCard(nonExistentHash)).rejects.toThrow(NotFoundError);
        });

        test('should throw NotFoundError when retrieving non-existent card', async () => {
            const nonExistentHash = 'non_existent_hash_123';
            await expect(client.getCard(nonExistentHash)).rejects.toThrow(NotFoundError);
        });
    });

    describe('Advanced Configuration', () => {
        test('should allow custom base URL and timeout', () => {
            const config = new MCardClientConfig()
                .withBaseUrl('http://localhost:8080')
                .withTimeout(10000)
                .build();

            const customClient = new MCardClient(config);
            expect(customClient._baseURL).toBe('http://localhost:8080');
        });

        test('should handle missing or invalid configuration', () => {
            const client = new MCardClient({});
            expect(client._baseURL).toBeDefined();
            expect(client._apiKey).toBeDefined();
        });

        test('should allow custom logger', () => {
            const mockLogger = {
                debug: jest.fn(),
                info: jest.fn(),
                warn: jest.fn(),
                error: jest.fn()
            };

            const client = new MCardClient({ logger: mockLogger });
            client._log('info', 'Test log');
            expect(mockLogger.info).toHaveBeenCalledWith('Test log');
        });
    });

    describe('Client Configuration', () => {
        test('should allow custom base URL', () => {
            const client = new MCardClient({ baseURL: 'http://custom-host:1234' });
            expect(client._baseURL).toBe('http://custom-host:1234');
        });

        test('should use default configuration when no options provided', () => {
            const client = new MCardClient();
            expect(client._baseURL).toBeDefined();
            expect(client._apiKey).toBeDefined();
        });
    });

    describe('Card Operations', () => {
        beforeEach(async () => {
            await client.deleteAllCards();
        });

        test('should create a card successfully', async () => {
            const card = await client.createCard('test content');
            expect(card.content).toBe('test content');
            expect(card.hash).toBeDefined();
        });

        test('should get a card successfully', async () => {
            const createdCard = await client.createCard('test content');
            const retrievedCard = await client.getCard(createdCard.hash);
            expect(retrievedCard.content).toBe('test content');
        });

        test('should delete a card successfully', async () => {
            // Ensure server is ready and clean
            await client.deleteAllCards();
            
            // Create a card first
            const content = 'test content';
            const card = await client.createCard(content);
            const hash = card.hash;
            
            // Verify card was created
            const retrievedCard = await client.getCard(hash);
            expect(retrievedCard).toBeDefined();
            expect(retrievedCard.content).toBe(content);
            
            // Attempt to delete the card with more robust error handling
            try {
                const result = await client.deleteCard(hash);
                console.log('Delete result:', result);
                expect(result).toBe(true);
                
                // Verify card was deleted by checking for a 404
                await expect(client.getCard(hash)).rejects.toThrow();
            } catch (error) {
                console.error('Delete card test failed:', error);
                throw error;
            }
        });

        test('should return true when deleting a non-existent card', async () => {
            const client = new MCardClient();
            const result = await client.deleteCard('non_existent_hash');
            // Expect true since the server returns 204 No Content
            expect(result).toBe(true);
        });
    });

    describe('List and Search Cards', () => {
        beforeEach(async () => {
            await client.deleteAllCards();
            await client.createCard('Python programming');
            await client.createCard('Web development');
            await client.createCard('Cloud computing');
        });

        test('should list cards with default parameters', async () => {
            const result = await client.listCards();
            expect(result.cards.length).toBeGreaterThan(0);
            expect(result.totalCards).toBe(3);
        });

        test('should search cards by content', async () => {
            const result = await client.listCards({ query: 'Python' });
            expect(result.cards.length).toBe(1);
            expect(result.cards[0].content).toContain('Python');
        });

        test('should search cards by hash', async () => {
            const createdCard = await client.createCard('Unique content');
            const result = await client.listCards({ 
                query: createdCard.hash, 
                searchHash: true 
            });
            expect(result.cards.length).toBe(1);
            expect(result.cards[0].hash).toBe(createdCard.hash);
        });

        test('should search cards by time', async () => {
            const result = await client.listCards({ 
                query: '2024-12', 
                searchTime: true 
            });
            expect(result.cards.length).toBeGreaterThan(0);
        });

        test('should handle pagination', async () => {
            const result = await client.listCards({ 
                page: 1, 
                pageSize: 2 
            });
            expect(result.cards.length).toBe(2);
            expect(result.totalCards).toBe(3);
            expect(result.totalPages).toBe(2);
        });
    });

    describe('MCard Client Advanced Content Tests', () => {
        let client;
        let savedCardHashes = [];

        beforeAll(async () => {
            // Use default configuration to ensure correct API key
            client = new MCardClient();
            
            // Attempt to delete all cards, but don't fail if it doesn't work
            try {
                await client.deleteAllCards();
            } catch (error) {
                console.warn('Could not delete all cards:', error.message);
            }
        });

        afterAll(async () => {
            // Do not delete all cards, keep them for future reference
            console.log('Saved card hashes:', savedCardHashes);
        });

        test('should create cards with various binary content types', async () => {
            const binaryContents = [
                Buffer.from('binary data'),
                new Uint8Array([1, 2, 3, 4]),
                new ArrayBuffer(8)
            ];

            const savedHashes = [];
            for (const content of binaryContents) {
                const card = await client.createCard(content);
                savedHashes.push(card.hash);
            }

            // Verify cards were created
            expect(savedHashes.length).toBe(binaryContents.length);
        });

        test('should handle complex nested content', async () => {
            const nestedContent = {
                key1: 'value1',
                key2: {
                    nestedKey: 'nestedValue'
                },
                array: [1, 2, 3]
            };

            const card = await client.createCard(nestedContent);
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
        });

        test('should handle large content near size limits', async () => {
            const largeContent = 'a'.repeat(900000);  // Close to max length
            const card = await client.createCard(largeContent);
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
        });
    });
});
