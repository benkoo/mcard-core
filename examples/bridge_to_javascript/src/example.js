const { MCardClient } = require('./client');
require('dotenv').config();

async function main() {
    try {
        // Initialize client with debug mode and custom configuration
        const client = new MCardClient({
            debug: true,
            timeout: 10000,
            maxRetries: 3,
            maxHistorySize: 50
        });

        // Check server health
        console.log('Checking server health...');
        const health = await client.checkHealth();
        console.log('Server health:', health);

        // Create cards with content and metadata
        console.log('\nCreating cards...');
        const cards = await Promise.all([
            client.createCard({
                content: 'Hello, World!',
                metadata: { type: 'greeting', language: 'english' }
            }),
            client.createCard({
                content: '<h1>HTML Content</h1>',
                metadata: { type: 'html', format: 'markup' }
            }),
            client.createCard({
                content: 'console.log("JavaScript Content");',
                metadata: { type: 'code', language: 'javascript' }
            })
        ]);
        console.log('Created cards:', cards);

        // Demonstrate pagination with search
        console.log('\nListing cards with pagination...');
        const page1 = await client.listCards({ page: 1, pageSize: 2, search: '' });
        console.log('Page 1:', page1);
        
        if (page1.has_next) {
            const page2 = await client.listCards({ page: 2, pageSize: 2 });
            console.log('Page 2:', page2);
        }

        // Get all cards at once
        console.log('\nGetting all cards...');
        const allCards = await client.getAllCards();
        console.log('Total cards:', allCards.length);

        // Get a specific card
        const firstCardHash = cards[0].hash;
        console.log(`\nGetting card with hash ${firstCardHash}...`);
        const retrievedCard = await client.getCard(firstCardHash);
        console.log('Retrieved card:', retrievedCard);

        // Delete a specific card
        console.log(`\nDeleting card with hash ${firstCardHash}...`);
        await client.deleteCard(firstCardHash);
        console.log('Card deleted successfully');

        // Show metrics
        console.log('\nClient metrics:');
        console.log(client.getMetrics());

        // Show request history
        console.log('\nRequest history:');
        const history = client.getRequestHistory();
        console.log(`Last ${history.length} requests:`, history);

        // Clean up - delete all remaining cards
        console.log('\nCleaning up - deleting all cards...');
        await client.deleteCards();
        console.log('All cards deleted');

        // Reset metrics
        console.log('\nResetting metrics...');
        client.resetMetrics();
        console.log('Final metrics after reset:', client.getMetrics());

    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
}

// Run the example
if (require.main === module) {
    main().catch(console.error);
}
