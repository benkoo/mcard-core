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

## Enhanced MCard Client Design

### Overview
The `EnhancedMCardClient` is a sophisticated JavaScript client for interacting with the MCard service, providing advanced features beyond basic HTTP requests.

### Key Design Principles

#### 1. Error Handling
- Implements custom error classes for granular error tracking:
  - `ValidationError`: For input validation failures
  - `AuthorizationError`: For authentication-related issues
  - `NetworkError`: For connection problems
  - `NotFoundError`: For resource not found scenarios
  - `MCardError`: Generic server-side errors

#### 2. Metrics Tracking
- Built-in metrics collection system to monitor:
  - Total number of requests
  - Successful and failed request counts
  - Detailed error type breakdown
- Supports request history tracking in debug mode
- Provides methods to reset metrics

#### 3. Content Validation
- Flexible content validation mechanism
  - Default validators for content length
  - Supports custom validator functions
  - Prevents invalid content from being submitted

#### 4. Logging and Debugging
- Configurable logging levels
- Debug mode for detailed request/response tracking
- Customizable console logging

#### 5. Configuration Flexibility
- Supports custom configuration options:
  - Base URL
  - API Key
  - Timeout settings
  - Debug mode
  - Custom content validators

### Usage Example

```javascript
const client = new EnhancedMCardClient({
    baseURL: 'http://localhost:5320',
    apiKey: 'your-api-key',
    debug: true,
    contentValidators: [
        (content) => {
            if (content.includes('forbidden')) {
                throw new ValidationError('Forbidden content');
            }
        }
    ]
});

// Create a card
const cardHash = await client.createCard('My content');

// Get metrics
const metrics = client.getMetrics();
console.log(metrics.totalRequests); // Number of total requests
```

### Error Handling Strategy
- Automatically throws specific error types based on HTTP status codes
- Provides detailed error information for debugging
- Supports catching and handling specific error types

### Performance Considerations
- Lightweight wrapper around Axios
- Minimal overhead for metrics and validation
- Configurable timeout to prevent long-running requests

### Extensibility
- Open for extension through custom validators
- Easily mockable for testing
- Supports different content types and validation strategies

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
