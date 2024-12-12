const dotenv = require('dotenv');
dotenv.config({ path: '../.env' });

const MCardServiceProxy = require('../src/mcard_service_proxy');
const MCardServiceClinic = require('../src/mcard_service_clinic');
const axios = require('axios');

describe('MCard Service Validation', () => {
    let mcardService;

    beforeAll(async () => {
        // Create a new service instance for each test
        mcardService = new MCardServiceProxy();
        await mcardService.startServer(); // Start the server
    });

    afterAll(async () => {
        jest.setTimeout(60000); // Set timeout to 60 seconds for debugging
        console.log('Stopping the server...');
        await mcardService.stopServer(); // Stop the server after tests
        console.log('Server stopped successfully.');
    });

    describe('API Key Validation', () => {
        it('validates API keys correctly', () => {
            const apiKey = process.env.MCARD_API_KEY;
            expect(mcardService.validateApiKey(apiKey)).toBe(true);
            expect(mcardService.validateApiKey('')).toBe(false);
            expect(mcardService.validateApiKey(null)).toBe(false);
        });
    });

    describe('Port Number Validation', () => {
        it('validates port numbers', () => {
            const port = parseInt(process.env.MCARD_API_PORT, 10);
            expect(mcardService.validatePortNumber(port)).toBe(true);
            expect(mcardService.validatePortNumber(0)).toBe(true);
            expect(mcardService.validatePortNumber(65535)).toBe(true);
            
            expect(mcardService.validatePortNumber(-1)).toBe(false);
            expect(mcardService.validatePortNumber(65536)).toBe(false);
            expect(mcardService.validatePortNumber(3.14)).toBe(false);
        });
    });

    describe('Database Path Validation', () => {
        it('validates database paths', () => {
            const mcardService = MCardServiceProxy.getInstance();

            // Valid paths
            expect(mcardService.validateDatabasePath('/path/to/database.db')).toBe(true);
            expect(mcardService.validateDatabasePath('C:\\path\\to\\database.sqlite')).toBe(true);
            expect(mcardService.validateDatabasePath('/Users/username/data/mydb.sqlite3')).toBe(true);

            // Invalid paths
            expect(mcardService.validateDatabasePath('')).toBe(false);
            expect(mcardService.validateDatabasePath(null)).toBe(false);
            expect(mcardService.validateDatabasePath('invalid_file')).toBe(false);
            expect(mcardService.validateDatabasePath(' ')).toBe(false);
            expect(mcardService.validateDatabasePath('/path/without/extension')).toBe(false);
        });
    });

    describe('Network Connectivity', () => {
        it('checks network connectivity', async () => {
            const isConnected = await mcardService.checkNetworkConnectivity();
            expect(isConnected).toBe(true);
        });
    });
});
