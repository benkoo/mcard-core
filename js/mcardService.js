import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Function to create a new card
export async function createCard(content) {
    try {
        const response = await axios.post(`${API_BASE_URL}/cards/`, { content });
        return response.data;
    } catch (error) {
        console.error('Failed to create card:', error);
        throw error;
    }
}

// Function to get a card by hash
export async function getCard(hash) {
    try {
        const response = await axios.get(`${API_BASE_URL}/cards/${hash}`);
        return response.data;
    } catch (error) {
        console.error('Failed to get card:', error);
        throw error;
    }
}

// Function to list cards with pagination
export async function listCards(limit = 10, offset = 0) {
    try {
        const response = await axios.get(`${API_BASE_URL}/cards/`, {
            params: { limit, offset }
        });
        return response.data;
    } catch (error) {
        console.error('Failed to list cards:', error);
        throw error;
    }
}

// Function to delete a card by hash
export async function deleteCard(hash) {
    try {
        const response = await axios.delete(`${API_BASE_URL}/cards/${hash}`);
        return response.data;
    } catch (error) {
        console.error('Failed to delete card:', error);
        throw error;
    }
}
