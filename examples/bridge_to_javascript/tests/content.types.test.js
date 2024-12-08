const { MCardClient } = require('../src/client');
const { TestEnvironment } = require('./utils/test-utils');
const fs = require('fs').promises;
const path = require('path');

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
        await client.deleteCards();
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
    });

    describe('Binary Content', () => {
        it('should handle base64 encoded binary', async () => {
            const binaryContent = Buffer.from('Binary Test Data').toString('base64');
            const card = await client.createCard({ binary: binaryContent });
            const retrieved = await client.getCard(card.hash);
            expect(JSON.parse(retrieved.content)).toEqual({ binary: binaryContent });
        });
    });
});