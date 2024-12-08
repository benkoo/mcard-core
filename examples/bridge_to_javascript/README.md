# MCard JavaScript Bridge

A lightweight Node.js client library for interacting with the MCard Core content-addressable storage system.

## Features

- Simple and intuitive API
- Promise-based async/await interface
- Robust input validation
- Comprehensive error handling
- Basic metrics tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcard-core.git
cd mcard-core/examples/bridge_to_javascript

2. Install dependencies:

```bash
npm install

3. Usage
The library provides a straightforward client for interacting with the MCard Core server:

const { MCardClient } = require('./src/client');

// Initialize client with server URL
const client = new MCardClient('http://localhost:5320');

// Create a card
const card = await client.createCard({ 
    content: 'Hello, World!',
    metadata: { type: 'greeting' }
});

// Get a card by hash (requires hash)
const retrievedCard = await client.getCard(card.hash);

// Delete a card (requires hash)
await client.deleteCard(card.hash);

4. Error Handling
The client includes robust error handling:

Mandatory input validation for getCard and deleteCard
Specific error messages for different scenarios
Throws "Hash is required" when no hash is provided
Provides clear 404 error messages for non-existent cards
Tracks network and validation errors via metrics
Example of input validation:


```js
try {
    await client.getCard();  // Throws an error
} catch (error) {
    console.error(error.message); // "Hash is required"
}

5. Testing
The test suite uses Jest and covers:

Error handling scenarios
Input validation
Metrics tracking
Client method functionality

Run tests with:

```bash
# Run all tests
npm test

# Generate coverage report
npm test -- --coverage

6. Metrics
The client provides basic request metrics:

Total number of requests
Successful requests
Failed requests
Retrieve metrics:

```js
const metrics = client.getMetrics();
console.log(metrics.totalRequests);
console.log(metrics.successfulRequests);


API Methods
createCard(content): Create a new card
getCard(hash): Retrieve a card (requires hash)
deleteCard(hash): Delete a card (requires hash)
getMetrics(): Get request metrics
Key Design Principles
Single request attempt per method call
No automatic retries
Comprehensive input validation
Transparent error reporting
Lightweight metrics tracking
