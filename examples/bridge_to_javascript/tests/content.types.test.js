const { MCardClient } = require('../src/client');
const { TestEnvironment } = require('./utils/test-utils');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios'); // Add axios import

describe('MCard Client Content Types', () => {
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
        
        // Delete all existing cards before each test
        try {
            await axios.delete('http://localhost:5320/cards', {
                headers: { 'X-API-Key': 'dev_key_123' },
                timeout: 1000
            });
        } catch (error) {
            console.warn('Failed to delete cards before test:', error.message);
        }
    });

    describe('Text Content', () => {
        it('should handle plain text', async () => {
            const content = 'Hello, World!';
            const card = await client.createCard(content);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(content);
        });

        it('should handle long text', async () => {
            const longText = 'A'.repeat(10000);
            const card = await client.createCard(longText);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(longText);
        });

        it('should handle special characters', async () => {
            const specialContent = '!@#$%^&*()_+{}:"<>?`~';
            const card = await client.createCard(specialContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(specialContent);
        });

        it('should handle multi-language text', async () => {
            const multiLangText = '你好世界 Hello World こんにちは セカイ';
            const card = await client.createCard(multiLangText);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(multiLangText);
        });

        // Removed empty string test for now
    });

    describe('Structured Content', () => {
        it('should handle JSON objects', async () => {
            const content = {
                name: 'Test Object',
                values: [1, 2, 3],
                nested: { key: 'value' }
            };
            const card = await client.createCard(content);
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual(content);
        });

        it('should handle complex nested structures', async () => {
            const complexContent = {
                level1: {
                    level2: {
                        level3: {
                            array: [1, 2, { nested: 'value' }]
                        }
                    }
                }
            };
            const card = await client.createCard(complexContent);
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual(complexContent);
        });

        it('should handle arrays of mixed types', async () => {
            const mixedArray = [
                'string',
                42, 
                true, 
                null, 
                { key: 'value' }, 
                [1, 2, 3]
            ];
            const card = await client.createCard(mixedArray);
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual(mixedArray);
        });

        it('should handle deeply nested objects', async () => {
            const deepNesting = {
                a: { 
                    b: { 
                        c: { 
                            d: { 
                                e: { 
                                    f: 'deep value' 
                                } 
                            } 
                        } 
                    } 
                }
            };
            const card = await client.createCard(deepNesting);
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual(deepNesting);
        });
    });

    describe('Binary Content', () => {
        it('should handle base64 encoded binary', async () => {
            const binaryContent = Buffer.from('Binary Test Data').toString('base64');
            const card = await client.createCard({ binary: binaryContent });
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual({ binary: binaryContent });
        });

        it('should handle large base64 encoded files', async () => {
            const largeBinaryContent = Buffer.from('A'.repeat(1024 * 1024)).toString('base64'); // 1MB
            const card = await client.createCard({ largeBinary: largeBinaryContent });
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual({ largeBinary: largeBinaryContent });
        });

        it('should handle multiple binary files', async () => {
            const multiFileBinary = {
                file1: Buffer.from('First File').toString('base64'),
                file2: Buffer.from('Second File').toString('base64')
            };
            const card = await client.createCard(multiFileBinary);
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual(multiFileBinary);
        });
    });

    describe('Edge Case Content', () => {
        it('should handle null content', async () => {
            await expect(client.createCard(null)).rejects.toThrow();
        });

        it('should handle undefined content', async () => {
            await expect(client.createCard(undefined)).rejects.toThrow();
        });

        it('should handle circular references', async () => {
            const circularObj = { ref: null };
            circularObj.ref = circularObj;

            await expect(client.createCard(circularObj)).rejects.toThrow();
        });

        it('should handle whitespace-only content', async () => {
            await expect(client.createCard('   ')).rejects.toThrow('Content cannot be empty');
        });

        it('should handle numeric content', async () => {
            const numericContent = 42;
            const card = await client.createCard(numericContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe('42');
        });

        it('should handle boolean content', async () => {
            const booleanContent = true;
            const card = await client.createCard(booleanContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe('true');
        });
    });

    describe('Error Handling', () => {
        it('should reject empty string content', async () => {
            await expect(client.createCard('')).rejects.toThrow();
        });

        it('should handle content with special characters and escaping', async () => {
            const escapedContent = 'Line 1\nLine 2\tTab\r\nCarriage Return';
            const card = await client.createCard(escapedContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(escapedContent);
        });
    });
});