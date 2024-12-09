const fs = require('fs');
const path = require('path');
const MCardServiceProxy = require('../src/mcard_service_proxy');

// Helper function to generate test content
const generateTestContent = (type) => {
    switch(type) {
        case 'text':
            return 'Sample text content for MCard';
        case 'json':
            return JSON.stringify({ 
                name: 'Test Card', 
                version: '1.0', 
                tags: ['test', 'sample'] 
            });
        case 'xml':
            return `<?xml version="1.0" encoding="UTF-8"?>
<mcard>
    <title>Test XML Card</title>
    <description>Sample XML content</description>
</mcard>`;
        case 'base64':
            // Base64 encoded "Hello World"
            return 'SGVsbG8gV29ybGQ=';
        default:
            return null;
    }
};

// Helper function to generate binary file content
const generateBinaryContent = (type) => {
    const testDataDir = path.join(__dirname, 'test_data');
    
    // Ensure test data directory exists
    if (!fs.existsSync(testDataDir)) {
        fs.mkdirSync(testDataDir);
    }

    const filePath = path.join(testDataDir, `sample.${type}`);
    
    // If file already exists, return its path
    if (fs.existsSync(filePath)) {
        return filePath;
    }

    // Generate sample files
    switch(type) {
        case 'pdf':
            // Minimal PDF content
            fs.writeFileSync(filePath, '%PDF-1.5\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>');
            break;
        case 'svg':
            fs.writeFileSync(filePath, `<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
</svg>`);
            break;
        case 'jpg':
            // Minimal JPG header
            fs.writeFileSync(filePath, Buffer.from([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46]));
            break;
        case 'png':
            // PNG file signature
            fs.writeFileSync(filePath, Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]));
            break;
        case 'xml':
            fs.writeFileSync(filePath, `<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item>Sample XML Binary Content</item>
</root>`);
            break;
        default:
            throw new Error(`Unsupported file type: ${type}`);
    }

    return filePath;
};

describe('MCard Content Operations', () => {
    let mcardService;
    let serverStarted = false;

    beforeAll(async () => {
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

    // Utility function to wait for server readiness
    const waitForServer = async () => {
        if (!serverStarted) {
            throw new Error('Server not started');
        }
    };

    // Text Content Tests
    describe('Text Content Cards', () => {
        beforeEach(waitForServer);

        it('should create a card with plain text', async () => {
            const textContent = generateTestContent('text');
            const card = await mcardService.createCard(textContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(textContent);
        });

        it('should create a card with JSON content', async () => {
            const jsonContent = generateTestContent('json');
            const card = await mcardService.createCard(jsonContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(jsonContent);
        });

        it('should create a card with XML content', async () => {
            const xmlContent = generateTestContent('xml');
            const card = await mcardService.createCard(xmlContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(xmlContent);
        });
    });

    // Binary Content Tests
    describe('Binary Content Cards', () => {
        beforeEach(waitForServer);

        it('should create a card with PDF content', async () => {
            const pdfPath = generateBinaryContent('pdf');
            const pdfContent = fs.readFileSync(pdfPath, 'base64');
            
            const card = await mcardService.createCard(pdfContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(pdfContent);
        });

        it('should create a card with SVG content', async () => {
            const svgPath = generateBinaryContent('svg');
            const svgContent = fs.readFileSync(svgPath, 'base64');
            
            const card = await mcardService.createCard(svgContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(svgContent);
        });

        it('should create a card with JPG content', async () => {
            const jpgPath = generateBinaryContent('jpg');
            const jpgContent = fs.readFileSync(jpgPath, 'base64');
            
            const card = await mcardService.createCard(jpgContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(jpgContent);
        });

        it('should create a card with PNG content', async () => {
            const pngPath = generateBinaryContent('png');
            const pngContent = fs.readFileSync(pngPath, 'base64');
            
            const card = await mcardService.createCard(pngContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(pngContent);
        });
    });

    // Large Content and Edge Cases
    describe('Large and Edge Case Content', () => {
        beforeEach(waitForServer);

        it('should handle large text content', async () => {
            const largeTextContent = 'x'.repeat(1024 * 1024); // 1MB of text
            const card = await mcardService.createCard(largeTextContent);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(largeTextContent);
        });

        it('should handle base64 encoded content', async () => {
            const base64Content = generateTestContent('base64');
            const card = await mcardService.createCard(base64Content);
            
            expect(card).toBeDefined();
            expect(card.hash).toBeTruthy();
            expect(card.content).toBe(base64Content);
        });

        it('should handle empty content', async () => {
            await expect(mcardService.createCard('')).rejects.toThrow();
        });
    });

    // Retrieval and Listing Tests
    describe('Card Retrieval and Listing', () => {
        let createdCardHash;

        beforeEach(async () => {
            // Ensure server is ready
            await waitForServer();

            // Create a card to retrieve
            const testContent = generateTestContent('text');
            const card = await mcardService.createCard(testContent);
            createdCardHash = card.hash;
        });

        it('should retrieve a specific card', async () => {
            const retrievedCard = await mcardService.getCard(createdCardHash);
            
            expect(retrievedCard).toBeDefined();
            expect(retrievedCard.hash).toBe(createdCardHash);
        });

        it('should list cards', async () => {
            const cardList = await mcardService.listCards();
            
            expect(cardList).toBeDefined();
            expect(cardList.items).toBeDefined();
            expect(Array.isArray(cardList.items)).toBe(true);
            expect(cardList.items.length).toBeGreaterThan(0);
        });
    });

    // Error Handling
    describe('Error Handling in Card Operations', () => {
        beforeEach(waitForServer);

        it('should handle retrieving non-existent card', async () => {
            await expect(mcardService.getCard('non_existent_hash'))
                .rejects.toThrow();
        });
    });
});
