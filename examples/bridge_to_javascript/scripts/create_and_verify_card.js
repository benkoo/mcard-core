require('dotenv').config({ path: '../.env' });
const MCardServiceProxy = require('../src/mcard_service_proxy');
const fs = require('fs');
const path = require('path');

async function createAndVerifyCard() {
    try {
        // Create service proxy
        const proxy = new MCardServiceProxy();

        // Detailed logging of configuration
        console.log('Configuration:', JSON.stringify(proxy.config, null, 2));

        // Verify database directory
        const dbDir = path.dirname(proxy.config.dbPath);
        console.log('Database Directory:', dbDir);
        console.log('Database Directory Exists:', fs.existsSync(dbDir));

        // Create directory if it doesn't exist
        if (!fs.existsSync(dbDir)) {
            fs.mkdirSync(dbDir, { recursive: true });
            console.log('Created database directory');
        }

        // Create a test card
        const testCard = {
            content: Buffer.from('Test MCard Content').toString('base64'),
            metadata: {
                hash: 'test_hash_123',
                g_time: Date.now()
            }
        };

        console.log('Test Card Payload:', JSON.stringify(testCard, null, 2));

        console.log('Attempting to create card...');
        const createResponse = await proxy.createCard(testCard);
        console.log('Card creation response:', createResponse);

        // List cards to verify
        console.log('Attempting to list cards...');
        const listResponse = await proxy.listCards();
        console.log('Total cards:', listResponse.items.length);
        
        // Decode and print card contents
        listResponse.items.forEach((card, index) => {
            console.log(`Card ${index + 1}:`);
            console.log('  Encoded Content:', card.content);
            console.log('  Decoded Content:', Buffer.from(card.content, 'base64').toString('utf-8'));
            console.log('  Hash:', card.metadata.hash);
            console.log('  Timestamp:', card.metadata.g_time);
            console.log('---');
        });

        // Verify database file
        console.log('Database path:', proxy.config.dbPath);
        console.log('Database exists:', fs.existsSync(proxy.config.dbPath));
        console.log('Database size:', fs.existsSync(proxy.config.dbPath) ? fs.statSync(proxy.config.dbPath).size : 'N/A');
    } catch (error) {
        console.error('Error in card creation/verification:', error);
        console.error('Detailed error:', JSON.stringify(error, Object.getOwnPropertyNames(error), 2));
    }
}

createAndVerifyCard();
