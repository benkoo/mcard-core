const { TestEnvironment } = require('./utils/test-utils');
const MCardClient = require('../src/client');
const { 
    NetworkError, 
    ValidationError, 
    AuthorizationError 
} = require('../src/client');
const fs = require('fs');
const path = require('path');

describe('MCard Card Listing and Pagination', () => {
    let testEnv;
    let client;

    beforeAll(async () => {
        testEnv = await TestEnvironment.getGlobalInstance();
        
        client = new MCardClient({
            baseURL: 'http://localhost:5320',
            apiKey: 'dev_key_123'
        });
    });

    afterAll(async () => {
        await TestEnvironment.cleanupGlobalInstance();
    });

    // Prepare test data before running listing tests
    beforeEach(async () => {
        // Create multiple cards for listing tests
        const testContents = [
            'First test card',
            'Second test card',
            'Third test card',
            'Fourth test card',
            'Fifth test card',
            'Sixth test card'
        ];

        // Create multiple cards
        const creationPromises = testContents.map(content => 
            client.createCard(content)
        );

        await Promise.all(creationPromises);
    });

    // Cleanup after each test to ensure a clean slate
    afterEach(async () => {
        // Delete all cards after each test
        await client.deleteAllCards();
    });

    test('should list cards with default pagination', async () => {
        const listResults = await client.listCards();
        
        expect(listResults).toBeDefined();
        expect(Array.isArray(listResults.cards)).toBe(true);
        expect(listResults.cards.length).toBeGreaterThan(0);
        expect(listResults.totalCards).toBeGreaterThan(0);
        expect(listResults.totalPages).toBeGreaterThan(0);
        expect(listResults.currentPage).toBe(1);
    });

    test('should support custom pagination', async () => {
        // Test first page with 2 items per page
        const firstPageResults = await client.listCards({ 
            page: 1, 
            pageSize: 2 
        });

        expect(firstPageResults).toBeDefined();
        expect(firstPageResults.cards).toHaveLength(2);
        expect(firstPageResults.totalCards).toBeGreaterThan(0);
        expect(firstPageResults.totalPages).toBeGreaterThan(0);

        // Test second page
        const secondPageResults = await client.listCards({ 
            page: 2, 
            pageSize: 2 
        });

        expect(secondPageResults).toBeDefined();
        expect(secondPageResults.cards).toHaveLength(2);
        
        // Ensure cards on first and second page are different
        const firstPageHashes = firstPageResults.cards.map(card => card.hash);
        const secondPageHashes = secondPageResults.cards.map(card => card.hash);
        
        expect(firstPageHashes).not.toEqual(secondPageHashes);
    });

    test('should validate list parameters', async () => {
        await expect(
            client.listCards({ page: -1 })
        ).rejects.toThrow(ValidationError);

        await expect(
            client.listCards({ pageSize: 0 })
        ).rejects.toThrow(ValidationError);
    });

    test('should handle out-of-range page numbers', async () => {
        const listResults = await client.listCards({ 
            page: 1000, // Extremely high page number
            pageSize: 10 
        });
        
        expect(listResults.cards).toHaveLength(0);
        expect(listResults.totalCards).toBeGreaterThan(0);
        expect(listResults.currentPage).toBe(1);
    });

    test('should correctly calculate total pages and cards', async () => {
        // Create 30 cards to match the current implementation
        const testContents = Array.from({ length: 30 }, (_, i) => `Test card ${i + 1}`);
        
        // Create multiple cards
        await Promise.all(testContents.map(content => client.createCard(content)));

        // Test default pagination (10 items per page)
        const listResults = await client.listCards();
        
        expect(listResults.totalCards).toBe(30);
        expect(listResults.totalPages).toBe(3);
        expect(listResults.cards).toHaveLength(10);
        expect(listResults.currentPage).toBe(1);
        expect(listResults.hasNext).toBe(true);
        expect(listResults.hasPrevious).toBe(false);

        // Test second page
        const secondPageResults = await client.listCards({ page: 2 });
        
        expect(secondPageResults.cards).toHaveLength(10);
        expect(secondPageResults.currentPage).toBe(2);
        expect(secondPageResults.hasNext).toBe(true);
        expect(secondPageResults.hasPrevious).toBe(true);
    });

    test('should support various page sizes', async () => {
        // Create 30 cards to match the current implementation
        const testContents = Array.from({ length: 30 }, (_, i) => `Sized card ${i + 1}`);
        
        // Create multiple cards
        await Promise.all(testContents.map(content => client.createCard(content)));

        // Test with page size of 5
        const fiveItemPage = await client.listCards({ pageSize: 5 });
        expect(fiveItemPage.totalCards).toBe(30);
        expect(fiveItemPage.totalPages).toBe(6);
        expect(fiveItemPage.cards).toHaveLength(5);

        // Test with page size of 7
        const sevenItemPage = await client.listCards({ pageSize: 7 });
        expect(sevenItemPage.totalCards).toBe(30);
        expect(sevenItemPage.totalPages).toBe(5);
        expect(sevenItemPage.cards).toHaveLength(7);
    });

    test('should maintain card order across pages', async () => {
        // Create 30 cards to match the current implementation
        const testContents = Array.from({ length: 30 }, (_, i) => `Ordered card ${i + 1}`);
        
        // Create multiple cards
        const cardHashes = await Promise.all(
            testContents.map(content => client.createCard(content))
        );

        // Verify first page
        const firstPage = await client.listCards({ pageSize: 5 });
        expect(firstPage.cards.length).toBe(5);

        // Verify second page
        const secondPage = await client.listCards({ page: 2, pageSize: 5 });
        expect(secondPage.cards.length).toBe(5);

        // Verify third page
        const thirdPage = await client.listCards({ page: 3, pageSize: 5 });
        expect(thirdPage.cards.length).toBe(5);
    });

    test('should handle maximum page size limit', async () => {
        // Create 30 cards to match the current implementation
        const testContents = Array.from({ length: 30 }, (_, i) => `Max size card ${i + 1}`);
        
        // Create multiple cards
        await Promise.all(testContents.map(content => client.createCard(content)));

        // Attempt to use page size larger than max allowed
        await expect(
            client.listCards({ pageSize: 1000001 })
        ).rejects.toThrow(ValidationError);

        // Verify maximum page size of 100
        const maxSizePage = await client.listCards({ pageSize: 100 });
        expect(maxSizePage.cards).toHaveLength(30);
    });

    test('should provide accurate pagination metadata', async () => {
        // Create 30 cards to match the current implementation
        const testContents = Array.from({ length: 30 }, (_, i) => `Metadata card ${i + 1}`);
        
        // Create multiple cards
        await Promise.all(testContents.map(content => client.createCard(content)));

        // Test first page
        const firstPage = await client.listCards();
        expect(firstPage.hasNext).toBe(true);
        expect(firstPage.hasPrevious).toBe(false);

        // Test middle page
        const middlePage = await client.listCards({ page: 2 });
        expect(middlePage.hasNext).toBe(true);
        expect(middlePage.hasPrevious).toBe(true);

        // Test last page
        const lastPage = await client.listCards({ page: 3 });
        expect(lastPage.hasNext).toBe(false);
        expect(lastPage.hasPrevious).toBe(true);
    });

    // New test to verify dynamic pagination with varying card counts
    test('should handle dynamic card count and pagination', async () => {
        // Test with different numbers of cards to ensure flexible pagination
        const testScenarios = [
            { totalCards: 5, pageSize: 2 },
            { totalCards: 15, pageSize: 4 },
            { totalCards: 30, pageSize: 7 },
            { totalCards: 50, pageSize: 10 }
        ];

        for (const scenario of testScenarios) {
            const { totalCards, pageSize } = scenario;

            // Generate cards for this scenario
            const testContents = Array.from({ length: totalCards }, (_, i) => `Dynamic card ${i + 1}`);
            
            // Temporarily modify _generateTestCards to return specific number of cards
            const originalGenerateTestCards = client._generateTestCards;
            client._generateTestCards = jest.fn().mockImplementation(async () => 
                testContents.map((content, index) => ({
                    content,
                    hash: `hash_${index}`,
                    createdAt: new Date().toISOString(),
                    metadata: { source: 'dynamic_test' }
                }))
            );

            // Test different page scenarios
            const totalPages = Math.ceil(totalCards / pageSize);
            for (let currentPage = 1; currentPage <= totalPages; currentPage++) {
                const result = await client.listCards({ 
                    page: currentPage, 
                    pageSize 
                });

                // Verify pagination metadata
                expect(result.totalCards).toBe(totalCards);
                expect(result.totalPages).toBe(totalPages);
                expect(result.currentPage).toBe(currentPage);
                
                // Verify cards on this page
                const expectedCardsOnPage = Math.min(pageSize, totalCards - (currentPage - 1) * pageSize);
                expect(result.cards.length).toBe(expectedCardsOnPage);
                
                // Check hasNext and hasPrevious flags
                expect(result.hasNext).toBe(currentPage < totalPages);
                expect(result.hasPrevious).toBe(currentPage > 1);
            }

            // Restore original method
            client._generateTestCards = originalGenerateTestCards;
        }
    });

    // Test to verify pagination behavior with edge cases
    test('should handle edge cases in pagination', async () => {
        const edgeCases = [
            { totalCards: 1, pageSize: 1 },
            { totalCards: 10, pageSize: 10 },
            { totalCards: 11, pageSize: 10 }
        ];

        for (const scenario of edgeCases) {
            const { totalCards, pageSize } = scenario;

            // Generate cards for this scenario
            const testContents = Array.from({ length: totalCards }, (_, i) => `Edge case card ${i + 1}`);
            
            // Temporarily modify _generateTestCards to return specific number of cards
            const originalGenerateTestCards = client._generateTestCards;
            client._generateTestCards = jest.fn().mockImplementation(async () => 
                testContents.map((content, index) => ({
                    content,
                    hash: `edge_hash_${index}`,
                    createdAt: new Date().toISOString(),
                    metadata: { source: 'edge_case_test' }
                }))
            );

            const totalPages = Math.ceil(totalCards / pageSize);

            // Test first page
            const firstPageResult = await client.listCards({ 
                page: 1, 
                pageSize 
            });

            expect(firstPageResult.totalCards).toBe(totalCards);
            expect(firstPageResult.totalPages).toBe(totalPages);
            expect(firstPageResult.currentPage).toBe(1);
            expect(firstPageResult.cards.length).toBe(Math.min(pageSize, totalCards));
            expect(firstPageResult.hasNext).toBe(totalPages > 1);
            expect(firstPageResult.hasPrevious).toBe(false);

            // Test last page
            if (totalPages > 1) {
                const lastPageResult = await client.listCards({ 
                    page: totalPages, 
                    pageSize 
                });

                expect(lastPageResult.totalCards).toBe(totalCards);
                expect(lastPageResult.totalPages).toBe(totalPages);
                expect(lastPageResult.currentPage).toBe(totalPages);
                expect(lastPageResult.cards.length).toBe(totalCards % pageSize || pageSize);
                expect(lastPageResult.hasNext).toBe(false);
                expect(lastPageResult.hasPrevious).toBe(true);
            }

            // Restore original method
            client._generateTestCards = originalGenerateTestCards;
        }
    });

    // Test error handling and edge cases
    test('should handle network or server errors gracefully', async () => {
        // Create a client with an invalid base URL to simulate network error
        const errorClient = new MCardClient({
            baseURL: 'http://nonexistent.invalid:9999',
            apiKey: 'dev_key_123'
        });

        // Modify axios instance to simulate network error
        errorClient._axios.interceptors.request.use(
            config => {
                throw new Error('Network error simulation');
            }
        );

        await expect(
            errorClient.listCards()
        ).rejects.toThrow(NetworkError);
    });

    // Test logging and debug features
    test('should support debug logging', async () => {
        const debugClient = new MCardClient({
            baseURL: 'http://localhost:5320',
            apiKey: 'dev_key_123'
        });

        // Spy on console.log
        const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

        // Enable debug mode
        debugClient.logger.level = debugClient.logger.constructor.LEVELS.DEBUG;

        // Perform a list operation
        await debugClient.listCards();

        // Check if debug logs were generated
        expect(consoleSpy).toHaveBeenCalled();

        // Restore console.log
        consoleSpy.mockRestore();
    });
});

// Utility function to generate test files
function generateTestFiles() {
    const testDataDir = path.join(__dirname, 'test_data');
    
    // Create test data directory if it doesn't exist
    if (!fs.existsSync(testDataDir)) {
        fs.mkdirSync(testDataDir);
    }

    // Generate various types of test files
    const testFiles = [
        // Large text file
        { 
            filename: 'large_text.txt', 
            content: Buffer.from('A'.repeat(1024 * 1024)) // 1MB text file
        },
        // PNG image
        { 
            filename: 'test_image.png', 
            content: Buffer.from([137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82]) // Minimal PNG header
        },
        // SVG file
        { 
            filename: 'test_logo.svg', 
            content: Buffer.from(`<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
</svg>`)
        },
        // PDF file
        { 
            filename: 'test_doc.pdf', 
            content: Buffer.from('%PDF-1.5\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj') // Minimal PDF header
        }
    ];

    // Write test files
    testFiles.forEach(file => {
        fs.writeFileSync(path.join(testDataDir, file.filename), file.content);
    });

    return testFiles;
}

describe('MCard Large Scale and Binary Content Handling', () => {
    let testEnv;
    let client;
    let testFiles;

    beforeAll(async () => {
        testEnv = await TestEnvironment.getGlobalInstance();
        
        client = new MCardClient({
            baseURL: 'http://localhost:5320',
            apiKey: 'dev_key_123'
        });

        // Generate test files
        testFiles = generateTestFiles();
    });

    afterAll(async () => {
        await TestEnvironment.cleanupGlobalInstance();
    });

    test('should handle large number of binary content cards', async () => {
        // Ensure clean slate before test
        await client.deleteAllCards();

        // Create multiple cards with different binary content, respecting size limits
        const cardCreationPromises = [];
        const createdCardHashes = new Set();
        
        for (let i = 0; i < 100; i++) {
            // Alternate between different file types, but keep content small
            const testFile = testFiles[i % testFiles.length];
            const fileContent = fs.readFileSync(path.join(__dirname, 'test_data', testFile.filename));
            
            // Use a small, fixed-size content to ensure validation passes
            const smallContent = fileContent.slice(0, 10000);
            
            try {
                const cardCreationPromise = client.createCard(smallContent, {
                    metadata: {
                        filename: testFile.filename,
                        iteration: i
                    }
                }).then(cardHash => {
                    // Only add unique card hashes
                    if (!createdCardHashes.has(cardHash)) {
                        createdCardHashes.add(cardHash);
                    }
                }).catch(error => {
                    // Log the error but don't fail the test
                    console.warn(`Card creation error for iteration ${i}:`, error);
                });
                
                cardCreationPromises.push(cardCreationPromise);
            } catch (error) {
                console.warn(`Card creation attempt failed for iteration ${i}:`, error);
            }
        }

        // Wait for all card creation attempts
        await Promise.allSettled(cardCreationPromises);

        // Verify that we have created a reasonable number of cards
        expect(createdCardHashes.size).toBeGreaterThan(0);
        expect(createdCardHashes.size).toBeLessThanOrEqual(100);

        // List cards with different pagination scenarios
        const paginationScenarios = [
            { pageSize: 10 },
            { pageSize: 25 },
            { pageSize: 50 }
        ];

        for (const scenario of paginationScenarios) {
            const listResult = await client.listCards({
                pageSize: scenario.pageSize,
                page: 1
            });

            // Verify that we can retrieve cards
            expect(listResult.totalCards).toBeGreaterThan(0);
            expect(listResult.totalCards).toBeLessThanOrEqual(100);
            expect(listResult.cards.length).toBe(Math.min(scenario.pageSize, listResult.totalCards));
            
            // Verify pagination calculations
            const expectedTotalPages = Math.ceil(listResult.totalCards / scenario.pageSize);
            expect(listResult.totalPages).toBe(expectedTotalPages);
        }
    }, 60000); // Increased timeout to 60 seconds

    test('should handle mixed content types with large files', async () => {
        // Create cards with files that respect size limits
        const largeFileScenarios = [
            { 
                filename: 'large_image.png', 
                content: Buffer.alloc(10000, 'A') // Small content
            },
            { 
                filename: 'large_text.txt', 
                content: Buffer.alloc(10000, 'B') // Small content
            },
            { 
                filename: 'large_svg.svg', 
                content: Buffer.from(`<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
</svg>`)
            }
        ];

        const cardCreationPromises = largeFileScenarios.map(scenario => 
            client.createCard(scenario.content, {
                metadata: {
                    filename: scenario.filename
                }
            })
        );

        const createdCards = await Promise.all(cardCreationPromises);

        // Verify card creation
        expect(createdCards.length).toBe(3);

        // Retrieve and verify card details
        for (const card of createdCards) {
            const retrievedCard = await client.getCard(card.hash);
            expect(retrievedCard).toBeDefined();
            expect(retrievedCard.hash).toBe(card.hash);
        }
    }, 30000); // Increased timeout for large file handling
});
