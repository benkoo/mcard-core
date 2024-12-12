const fs = require('fs');
const path = require('path');
const MCardServiceProxy = require('../src/mcard_service_proxy');
const MCardServiceClinic = require('../src/mcard_service_clinic');

describe('MCard Persistent Database Tests', () => {
    let instance;

    beforeAll(async () => {
        // Reset any existing instance
        MCardServiceProxy.reset();

        // Create a new instance
        instance = MCardServiceProxy.getInstance();

        // Validate database path
        if (!MCardServiceClinic.validateDatabasePath(instance.config.dbPath)) {
            throw new Error('Invalid database path');
        }

        // Start the server
        await instance.startServer();
    });

    describe('Persistent Database Behavior', () => {
        it('should have a database file created', () => {
            console.log('Database Path SHOULD HAVE BEEN CREATED:', instance.config.dbPath);
            expect(fs.existsSync(instance.config.dbPath)).toBe(true);
        });
    }); // Closing the Persistent Database Behavior describe block

    afterAll(async () => {
        // Stop the server and reset the instance
        await instance.stopServer();
        MCardServiceProxy.reset();
    });

    describe('Persistent Database Behavior', () => {
        // Verify database file is created
        it('should have a database file created', () => {
            console.log('Database Path SHOULD HAVE BEEN CREATED:', instance.config.dbPath);
            expect(fs.existsSync(instance.config.dbPath)).toBe(true);
        });

        // Test persisting cards across test runs
        it('should persist cards across test runs', async () => {
            const testContent = JSON.stringify({ 
                key: 'Test persistent card content', 
                timestamp: new Date().toISOString() 
            });
            const card = await instance.createCard(testContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(typeof card.hash).toBe('string');
            expect(card.hash.length).toBeGreaterThan(0);
        });

        // Verify previously created cards can be retrieved
        it('should show previously created cards', async () => {
            const cards = await instance.listCards();
            
            expect(Array.isArray(cards)).toBe(true);
            expect(cards.length).toBeGreaterThan(0);
        });
    });

    describe('Database File Inspection', () => {
        it('should provide database file details', () => {
            const stats = fs.statSync(instance.config.dbPath);
            
            console.log('Database File Details:');
            console.log('Path:', instance.config.dbPath);
            console.log('Size:', stats.size, 'bytes');
            console.log('Created:', stats.birthtime);
            console.log('Modified:', stats.mtime);

            expect(stats.size).toBeGreaterThan(0);
        });
    });
});
