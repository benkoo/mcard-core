const MCardServiceProxy = require('../src/mcard_service_proxy');
const fs = require('fs');
const path = require('path');

// Set the correct API key before tests
process.env.MCARD_API_KEY = 'valid_test_key';

describe('MCard Persistent Database Tests', () => {
    let mcardService;
    let serverStarted = false;
    const dbPath = process.env.MCARD_DB_PATH ? 
        path.join(__dirname, '..', process.env.MCARD_DB_PATH) : 
        path.join(__dirname, '..', 'data', 'mcard.db');

    // Utility function to wait for server readiness
    const waitForServer = async () => {
        if (!serverStarted) {
            mcardService = MCardServiceProxy.getInstance();
            await mcardService.startServer();
            serverStarted = true;
        }
    };

    beforeAll(async () => {
        // Ensure the data directory exists
        const dataDir = path.dirname(dbPath);
        if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
        }

        // Reset environment variables for clean testing
        process.env.NODE_ENV = 'test';
        process.env.MCARD_API_KEY = 'valid_test_key';

        // Increase timeout for server startup
        jest.setTimeout(60000);

        // Start server using static method
        serverStarted = await MCardServiceProxy.startServer();

        // Get the singleton instance for further operations
        mcardService = MCardServiceProxy.getInstance();
    }, 60000);

    afterAll(async () => {
        // Stop the server after tests
        if (serverStarted) {
            await MCardServiceProxy.stopServer();
            MCardServiceProxy.reset();
        }
    }, 30000);

    describe('Persistent Database Behavior', () => {
        // Verify database file exists
        it('should have a database file created', () => {
            expect(fs.existsSync(dbPath)).toBe(true);
        });

        // Create multiple cards across different test runs
        it('should persist cards across test runs', async () => {
            // Create a unique card for this test run
            const testContent = `Persistent Test Card - ${new Date().toISOString()}`;
            const base64Content = Buffer.from(testContent).toString('base64');
            const createdCard = await mcardService.createCard(base64Content);

            expect(createdCard).toBeDefined();
            expect(createdCard.hash).toBeDefined();

            console.log('Created Card:', createdCard);

            // Retrieve the card to verify it was saved
            const retrievedCard = await mcardService.getCard(createdCard.hash);
            expect(retrievedCard).toBeDefined();
            
            console.log('Retrieved Card:', retrievedCard);
            
            // Check that the content is base64 encoded
            const decodedContent = Buffer.from(retrievedCard.content, 'base64').toString('utf-8');
            console.log('Decoded Content:', decodedContent);
            console.log('Original Test Content:', testContent);

            expect(decodedContent).toBe(testContent);
        });

        // List cards to show persistence
        it('should show previously created cards', async () => {
            const cardList = await mcardService.listCards();
            
            expect(cardList).toBeDefined();
            expect(cardList.items).toBeDefined();
            expect(Array.isArray(cardList.items)).toBe(true);
            expect(cardList.items.length).toBeGreaterThan(0);
        });
    });

    // Optional: Inspect database file details
    describe('Database File Inspection', () => {
        it('should provide database file details', () => {
            const stats = fs.statSync(dbPath);
            
            console.log('Database File Details:');
            console.log('Path:', dbPath);
            console.log('Created:', stats.birthtime.toISOString());
            console.log('Last Modified:', stats.mtime.toISOString());

            expect(fs.existsSync(dbPath)).toBe(true);
        });
    });
});
