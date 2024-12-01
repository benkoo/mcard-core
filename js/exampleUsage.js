import { createCard, getCard, listCards, deleteCard } from './mcardService.js';

// Example usage
async function exampleUsage() {
    try {
        // Create a new card
        const newCard = await createCard('This is a test card');
        console.log('Created Card:', newCard);

        // Get the card by hash
        const card = await getCard(newCard.hash);
        console.log('Retrieved Card:', card);

        // List cards
        const cards = await listCards();
        console.log('List of Cards:', cards);

        // Delete the card
        const deleteResponse = await deleteCard(newCard.hash);
        console.log(deleteResponse);
    } catch (error) {
        console.error('Error:', error);
    }
}

exampleUsage();
