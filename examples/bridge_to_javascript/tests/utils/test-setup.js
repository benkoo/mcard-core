const { MCardClient } = require('../../src/client');
const fs = require('fs');
const path = require('path');
const { config } = require('../config/test-config');
const axios = require('axios');

/**
 * Creates a test client with default or custom configuration
 */
function createTestClient(customConfig = {}) {
    return new MCardClient({
        apiKey: config.server.apiKey,
        baseUrl: `http://127.0.0.1:${config.server.port}`,
        ...customConfig
    });
}

/**
 * Creates a client with invalid credentials for testing error cases
 */
function createInvalidClient(customConfig = {}) {
    return new MCardClient({
        apiKey: 'invalid_key',
        baseUrl: `http://127.0.0.1:${config.server.port}`,
        ...customConfig
    });
}

/**
 * Cleans up all cards for a client with retry logic
 */
async function cleanupCards(client = null) {
    const { cleanup } = config.testSuite;
    if (!cleanup.enabled) return;

    if (!client) {
        client = createTestClient();
    }

    try {
        const cards = await client.listCards();
        for (const card of cards) {
            await client.deleteCard(card.hash);
        }
    } catch (error) {
        console.error('Error cleaning up cards:', error);
    }
}

/**
 * Creates a test directory if it doesn't exist
 */
function createTestDirectory(dirName = 'test-data') {
    const dirPath = path.join(__dirname, '..', '..', dirName);
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
    return dirPath;
}

/**
 * Cleans up a test directory and its contents
 */
function cleanupTestDirectory(dirPath) {
    if (fs.existsSync(dirPath)) {
        const files = fs.readdirSync(dirPath);
        for (const file of files) {
            const filePath = path.join(dirPath, file);
            fs.unlinkSync(filePath);
        }
        fs.rmdirSync(dirPath);
    }
}

/**
 * Creates sample test files of various types
 */
function createSampleFiles(testDir = config.testData.testDataDir) {
    if (!fs.existsSync(testDir)) {
        fs.mkdirSync(testDir, { recursive: true });
    }

    // Create text file
    fs.writeFileSync(
        path.join(testDir, 'sample.txt'),
        'This is a sample text file for testing.'
    );

    // Create HTML file
    fs.writeFileSync(
        path.join(testDir, 'sample.html'),
        '<html><body><h1>Sample HTML</h1></body></html>'
    );

    // Create JavaScript file
    fs.writeFileSync(
        path.join(testDir, 'sample.js'),
        'console.log("Sample JavaScript file");'
    );
}

module.exports = {
    createTestClient,
    createInvalidClient,
    cleanupCards,
    createTestDirectory,
    cleanupTestDirectory,
    createSampleFiles
};
