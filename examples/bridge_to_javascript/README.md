# MCard JavaScript Bridge

A lightweight Node.js client library for interacting with the MCard Core content-addressable storage system.

## Features

- Promise-based async/await interface
- Robust content validation
- Comprehensive error handling
- Specific error types for different scenarios
- Advanced logging and debugging
- Flexible configuration

## Installation

```bash
npm install mcard-js-bridge
```

## Quick Start

```javascript
const { MCardClient } = require('mcard-js-bridge');

// Initialize client with default configuration
const client = new MCardClient({
    baseURL: 'http://localhost:5320',
    apiKey: 'your_api_key'
});

// Create a card
const cardHash = await client.createCard('Hello, World!');
console.log(cardHash);

// Retrieve a card
const retrievedCard = await client.getCard(cardHash);

// Delete a card
await client.deleteCard(cardHash);
```

## Advanced Configuration

### Client Initialization

```javascript
const client = new MCardClient({
    baseURL: 'http://localhost:5320',    // Custom server URL
    apiKey: 'your-api-key',              // Optional API key
    timeout: 5000,                       // Request timeout (ms)
    contentValidators: [                 // Optional custom validators
        (content) => {
            // Custom validation logic
        }
    ]
});
```

## Content Validation

The client provides robust content validation:

- Detects binary vs. text content
- Limits content length to 1,000,000 characters
- Supports custom validation through `contentValidators`

## Error Handling

The MCard client offers comprehensive error handling with specific error types:

- `ValidationError`: Input validation failures
- `AuthorizationError`: Authentication issues
- `NetworkError`: Connection problems
- `NotFoundError`: Resource not found scenarios

### Error Handling Example

```javascript
try {
    await client.createCard('Very long content...'); 
} catch (error) {
    if (error instanceof ValidationError) {
        console.error('Content validation failed:', error.message);
    }
}
```

## Logging

The client supports configurable logging:

```javascript
const client = new MCardClient({
    debug: true  // Enables detailed logging
});
```

## Pagination Design

### Card Listing with Pagination

The `listCards()` method provides flexible pagination with the following key design principles:

#### Default Pagination
- Default page is `1`
- Default page size is `10`
- Configurable through method options or global constants

#### Pagination Parameters
- `page`: Specifies the current page number (default: 1)
- `pageSize`: Determines the number of cards per page (default: 10)
- Supports custom page sizes between 1 and 100

#### Pagination Metadata
Each `listCards()` call returns a result object with:
- `cards`: Array of cards for the current page
- `totalCards`: Total number of cards
- `totalPages`: Total number of pages
- `currentPage`: Current page number
- `hasNext`: Boolean indicating if more pages exist
- `hasPrevious`: Boolean indicating if previous pages exist

#### Example Usage

```javascript
// List first page with default 10 cards
const firstPage = await client.listCards();

// Custom pagination: 5 cards per page, second page
const customPage = await client.listCards({ 
    page: 2, 
    pageSize: 5 
});
```

#### Error Handling
- Invalid page numbers throw a `ValidationError`
- Out-of-range pages return an empty card list
- Provides graceful fallback mechanisms

#### Performance Considerations
- Efficient slice-based pagination
- Deterministic card selection across pages
- Minimal overhead for pagination operations

## API Methods

### `createCard(content, options = {})`
- Creates a new card with given content
- Validates content length and type
- Throws `ValidationError` for invalid content
- Returns card hash

### `getCard(hash)`
- Retrieves a card by its hash
- Throws `NotFoundError` if card doesn't exist

### `deleteCard(hash)`
- Deletes a card by its hash
- Throws `NotFoundError` if card doesn't exist

### `healthCheck()`
- Checks server connection status
- Returns boolean indicating server health

### `listCards(options = {})`
- Lists cards with pagination support
- Returns pagination metadata and card list
- Supports custom page and page size
- Handles out-of-range page scenarios gracefully

## Error Types

- `ValidationError`: Content validation failures
- `AuthorizationError`: API key or permission issues
- `NetworkError`: Connection or request problems
- `NotFoundError`: Card or resource not found

## Environment Variables

- `MCARD_API_KEY`: Default API key
- `MCARD_BASE_URL`: Default server base URL

## Recent Changes

### December 9, 2024 - Performance and Pagination Optimization

- **Pagination Limit Adjustment**: 
  - Reduced `MAX_PAGE_SIZE` from 1,000,000 to 1,000 in both `server.py` and `constants.js`
  - Improves server performance and prevents potential resource exhaustion
  - Ensures more controlled and predictable pagination behavior
  - Maintains existing test coverage and functionality

### Rationale

The previous maximum page size of 1,000,000 was unreasonably large and could potentially lead to:
- Excessive memory consumption
- Increased server load
- Potential performance bottlenecks
- Risk of unintentional large data retrievals

By setting a more reasonable limit of 1,000 items per page, we:
- Protect server resources
- Encourage more efficient data retrieval patterns
- Provide a sensible default for most use cases

## Contributing

Contributions are welcome! Please submit pull requests or open issues on our GitHub repository.
