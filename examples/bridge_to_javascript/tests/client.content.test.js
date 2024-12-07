const { MCardClient } = require('../src/client');
const { TestEnvironment } = require('./utils/test-utils');
const fs = require('fs').promises;
const path = require('path');

describe('MCard Client Content Tests', () => {
    let client;
    let testEnv;

    beforeAll(async () => {
        testEnv = new TestEnvironment();
        await testEnv.startServer();
        client = new MCardClient();
    });

    afterAll(async () => {
        await testEnv.stopServer();
    });

    beforeEach(async () => {
        // Clean up any existing cards
        await client.deleteCards();
        await new Promise(resolve => setTimeout(resolve, 200));
    });

    describe('Text Content', () => {
        it('should handle plain text content', async () => {
            const textContent = 'Hello, this is a plain text content!';
            const card = await client.createCard(textContent);
            expect(card.hash).toBeDefined();
            
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(textContent);
        });

        it('should handle large text content', async () => {
            const largeText = Array.from({ length: 1000 }, (_, i) => 
                `Line ${i}: This is a test line with some content.`
            ).join('\n');
            
            const card = await client.createCard(largeText);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(largeText);
        });

        it('should handle text content with special characters', async () => {
            const specialContent = '!@#$%^&*()_+-=[]{}|;:,.<>?`~\n\tTabbed\tContent';
            const card = await client.createCard(specialContent);
            const retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(specialContent);
        });
    });

    describe('Binary Content', () => {
        it('should handle small binary content', async () => {
            const binaryData = Buffer.from('Hello Binary World!', 'utf8');
            const base64Content = binaryData.toString('base64');
            
            const card = await client.createCard(base64Content);
            const retrieved = await client.getCard(card.hash);
            expect(Buffer.from(retrieved.content, 'base64').toString('utf8'))
                .toBe('Hello Binary World!');
        });

        it('should handle large binary content', async () => {
            // Create a 100KB binary file
            const largeBuffer = Buffer.alloc(100 * 1024);
            for (let i = 0; i < largeBuffer.length; i++) {
                largeBuffer[i] = i % 256;
            }
            
            const base64Content = largeBuffer.toString('base64');
            const card = await client.createCard(base64Content);
            const retrieved = await client.getCard(card.hash);
            
            const retrievedBuffer = Buffer.from(retrieved.content, 'base64');
            expect(retrievedBuffer.length).toBe(largeBuffer.length);
            expect(retrievedBuffer).toEqual(largeBuffer);
        });
    });

    describe('Card Operations', () => {
        it('should list all cards with pagination', async () => {
            // Create multiple cards
            const contents = [
                'First card content',
                'Second card content',
                'Third card content'
            ];
            
            await Promise.all(contents.map(content => client.createCard(content)));
            
            const result = await client.listCards({ page: 1, pageSize: 10 });
            expect(result.items.length).toBe(3);
            expect(result.total).toBe(3);
            expect(result.page).toBe(1);
        });

        it('should delete specific cards', async () => {
            const content = 'Card to be deleted';
            const card = await client.createCard(content);
            
            // Verify card exists
            let retrieved = await client.getCard(card.hash);
            expect(retrieved.content).toBe(content);
            
            // Delete the card
            await client.deleteCard(card.hash);
            
            // Verify card is deleted
            try {
                await client.getCard(card.hash);
                fail('Expected card to be deleted');
            } catch (error) {
                expect(error.message).toContain('404');
            }
        });

        it('should handle search functionality', async () => {
            const contents = [
                'Searchable content one',
                'Another searchable item',
                'Non-matching content'
            ];
            
            await Promise.all(contents.map(content => client.createCard(content)));
            
            const searchResults = await client.listCards({ page: 1, pageSize: 10, search: 'searchable' });
            expect(searchResults.items.length).toBe(2);
            searchResults.items.forEach(item => {
                expect(item.content.toLowerCase()).toContain('searchable');
            });
        });
    });
});
