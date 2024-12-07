const { MCardClient } = require('./client');
require('dotenv').config();

async function main() {
    try {
        // Initialize client
        const client = new MCardClient();

        // Check server health
        console.log('Checking server health...');
        const health = await client.checkHealth();
        console.log('Server health:', health);

        // Create some example cards
        console.log('\nCreating cards...');
        const cards = await Promise.all([
            client.createCard({ content: 'Hello, World!' }),
            client.createCard({ content: '<h1>HTML Content</h1>' }),
            client.createCard({ content: 'console.log("JavaScript Content");' })
        ]);
        console.log('Created cards:', cards);

        // List all cards
        console.log('\nListing all cards...');
        const allCards = await client.listCards();
        console.log('All cards:', allCards);

        // Get a specific card
        const firstCardHash = cards[0].hash;
        console.log(`\nGetting card with hash ${firstCardHash}...`);
        const retrievedCard = await client.getCard(firstCardHash);
        console.log('Retrieved card:', retrievedCard);

        // Delete a card
        console.log(`\nDeleting card with hash ${firstCardHash}...`);
        await client.deleteCard(firstCardHash);
        console.log('Card deleted successfully');

        // List cards again to verify deletion
        console.log('\nListing all cards after deletion...');
        const remainingCards = await client.listCards();
        console.log('Remaining cards:', remainingCards);

    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
}

// Run the example
if (require.main === module) {
    main().catch(console.error);
}
