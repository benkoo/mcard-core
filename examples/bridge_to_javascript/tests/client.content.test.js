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
        let testDataPath;

        beforeAll(() => {
            testDataPath = path.join(__dirname, 'test_data');
        });

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

        it('should handle PNG image content', async () => {
            const imageData = await fs.readFile(path.join(testDataPath, 'test.png'));
            const base64Content = imageData.toString('base64');
            
            const card = await client.createCard(base64Content);
            const retrieved = await client.getCard(card.hash);
            
            const retrievedBuffer = Buffer.from(retrieved.content, 'base64');
            expect(retrievedBuffer).toEqual(imageData);
        });

        it('should handle PDF document content', async () => {
            const pdfData = await fs.readFile(path.join(testDataPath, 'test.pdf'));
            const base64Content = pdfData.toString('base64');
            
            const card = await client.createCard(base64Content);
            const retrieved = await client.getCard(card.hash);
            
            const retrievedBuffer = Buffer.from(retrieved.content, 'base64');
            expect(retrievedBuffer).toEqual(pdfData);
        });

        it('should handle GIF image content', async () => {
            const gifData = await fs.readFile(path.join(testDataPath, 'test.gif'));
            const base64Content = gifData.toString('base64');
            
            const card = await client.createCard(base64Content);
            const retrieved = await client.getCard(card.hash);
            
            const retrievedBuffer = Buffer.from(retrieved.content, 'base64');
            expect(retrievedBuffer).toEqual(gifData);
        });

        it('should handle binary content with metadata', async () => {
            const imageData = await fs.readFile(path.join(testDataPath, 'test.png'));
            
            const card = await client.createCard({
                content: imageData.toString('base64')
            });
            
            const retrieved = await client.getCard(card.hash);
            const retrievedBuffer = Buffer.from(retrieved.content, 'base64');
            expect(retrievedBuffer).toEqual(imageData);
        });

        it('should handle multiple binary files in sequence', async () => {
            const files = ['test.png', 'test.pdf', 'test.gif'];
            const results = [];

            for (const file of files) {
                const data = await fs.readFile(path.join(testDataPath, file));
                const card = await client.createCard({
                    content: data.toString('base64')
                });
                results.push({ hash: card.hash, data });
            }

            for (const { hash, data } of results) {
                const retrieved = await client.getCard(hash);
                expect(Buffer.from(retrieved.content, 'base64')).toEqual(data);
            }
        });

        it('should handle concurrent binary file uploads', async () => {
            const files = ['test.png', 'test.pdf', 'test.gif'];
            const fileData = await Promise.all(
                files.map(file => fs.readFile(path.join(testDataPath, file)))
            );

            const uploadPromises = fileData.map(data =>
                client.createCard({
                    content: data.toString('base64')
                })
            );

            const cards = await Promise.all(uploadPromises);
            const retrievedCards = await Promise.all(
                cards.map(card => client.getCard(card.hash))
            );
            
            retrievedCards.forEach((card, i) => {
                expect(Buffer.from(card.content, 'base64')).toEqual(fileData[i]);
            });
        });
    });

    describe('Mixed Content Operations', () => {
        let testDataPath;

        beforeAll(() => {
            testDataPath = path.join(__dirname, 'test_data');
        });

        it('should handle mixed text and binary content storage', async () => {
            // Create text content
            const textContent = 'Hello, World!';
            const textCard = await client.createCard(textContent);
            
            // Create binary content
            const imageData = await fs.readFile(path.join(testDataPath, 'test.png'));
            const binaryCard = await client.createCard({
                content: imageData.toString('base64')
            });

            // Verify text content
            const retrievedText = await client.getCard(textCard.hash);
            expect(retrievedText.content).toBe(textContent);

            // Verify binary content
            const retrievedBinary = await client.getCard(binaryCard.hash);
            const retrievedBuffer = Buffer.from(retrievedBinary.content, 'base64');
            expect(retrievedBuffer).toEqual(imageData);
        });

        it('should handle deletion of mixed content', async () => {
            // Create mixed content
            const textContent = 'Delete me';
            const textCard = await client.createCard(textContent);
            
            const imageData = await fs.readFile(path.join(testDataPath, 'test.png'));
            const binaryCard = await client.createCard({
                content: imageData.toString('base64')
            });

            // Verify content exists
            let retrievedText = await client.getCard(textCard.hash);
            expect(retrievedText.content).toBe(textContent);

            let retrievedBinary = await client.getCard(binaryCard.hash);
            expect(Buffer.from(retrievedBinary.content, 'base64')).toEqual(imageData);

            // Delete content
            await client.deleteCard(textCard.hash);
            await client.deleteCard(binaryCard.hash);

            // Verify content is deleted
            await expect(client.getCard(textCard.hash)).rejects.toThrow();
            await expect(client.getCard(binaryCard.hash)).rejects.toThrow();
        });

        it('should handle concurrent mixed content operations', async () => {
            // Prepare mixed content
            const textContents = ['Text 1', 'Text 2', 'Text 3'];
            const imageData = await fs.readFile(path.join(testDataPath, 'test.png'));
            const pdfData = await fs.readFile(path.join(testDataPath, 'test.pdf'));
            
            // Create cards concurrently
            const createPromises = [
                ...textContents.map(text => client.createCard(text)),
                client.createCard({ content: imageData.toString('base64') }),
                client.createCard({ content: pdfData.toString('base64') })
            ];

            const cards = await Promise.all(createPromises);
            
            // Verify all content
            const getPromises = cards.map(card => client.getCard(card.hash));
            const retrievedCards = await Promise.all(getPromises);

            // Verify text content
            for (let i = 0; i < textContents.length; i++) {
                expect(retrievedCards[i].content).toBe(textContents[i]);
            }

            // Verify binary content
            const retrievedImage = Buffer.from(retrievedCards[3].content, 'base64');
            const retrievedPdf = Buffer.from(retrievedCards[4].content, 'base64');
            expect(retrievedImage).toEqual(imageData);
            expect(retrievedPdf).toEqual(pdfData);

            // Delete all content concurrently
            const deletePromises = cards.map(card => client.deleteCard(card.hash));
            await Promise.all(deletePromises);

            // Verify all content is deleted
            for (const card of cards) {
                await expect(client.getCard(card.hash)).rejects.toThrow();
            }
        });

        it('should handle listing of mixed content', async () => {
            // Create mixed content
            const textCard = await client.createCard('List test text');
            const imageData = await fs.readFile(path.join(testDataPath, 'test.png'));
            const binaryCard = await client.createCard({
                content: imageData.toString('base64')
            });

            // List all cards
            const { items } = await client.listCards();
            
            // Find our cards in the list
            const foundText = items.find(item => item.hash === textCard.hash);
            const foundBinary = items.find(item => item.hash === binaryCard.hash);

            // Verify content
            expect(foundText.content).toBe('List test text');
            expect(Buffer.from(foundBinary.content, 'base64')).toEqual(imageData);

            // Clean up
            await client.deleteCard(textCard.hash);
            await client.deleteCard(binaryCard.hash);
        });

        it('should handle search across mixed content', async () => {
            // Create searchable content
            const searchableText = 'Unique searchable text';
            const textCard = await client.createCard(searchableText);
            
            const imageData = await fs.readFile(path.join(testDataPath, 'test.png'));
            const binaryCard = await client.createCard({
                content: imageData.toString('base64')
            });

            // Search for text content
            const { items: searchResults } = await client.listCards({ search: 'searchable' });
            expect(searchResults.some(item => item.hash === textCard.hash)).toBe(true);
            
            // Clean up
            await client.deleteCard(textCard.hash);
            await client.deleteCard(binaryCard.hash);
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
