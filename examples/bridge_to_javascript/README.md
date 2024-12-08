# MCard JavaScript Bridge

A lightweight Node.js client library for interacting with the MCard Core content-addressable storage system.

## Features

- Promise-based async/await interface
- Robust input validation
- Comprehensive error handling
- Advanced logging and debugging
- Flexible configuration
- Specific error types for different scenarios

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
    debug: true
});

// Create a card
const card = await client.createCard('Hello, World!');
console.log(card.hash);

// Retrieve a card
const retrievedCard = await client.getCard(card.hash);

// Delete a card
await client.deleteCard(card.hash);
```

## Advanced Configuration

### Client Initialization

```javascript
const client = new MCardClient({
    baseURL: 'http://localhost:5320',    // Custom server URL
    apiKey: 'your-api-key',              // Optional API key
    timeout: 5000,                       // Request timeout (ms)
    debug: true,                         // Enable debug logging
    contentValidators: [                 // Optional custom validators
        (content) => {
            if (content.length > 1000000) {
                throw new ValidationError('Content too long');
            }
        }
    ]
});
```

## Error Handling

The MCard client provides comprehensive error handling with specific error types:

- `ValidationError`: Input validation failures
- `AuthorizationError`: Authentication issues
- `NetworkError`: Connection problems
- `NotFoundError`: Resource not found scenarios

### Error Handling Example

```javascript
try {
    await client.createCard(''); // Empty content
} catch (error) {
    if (error instanceof ValidationError) {
        console.error('Invalid content:', error.message);
    }
}
```

## Logging and Debugging

The client supports configurable logging levels:

```javascript
const client = new MCardClient({
    debug: true  // Enables detailed logging
});
```

## API Methods

### `createCard(content, metadata = {})`
- Creates a new card with given content and optional metadata
- Returns card hash
- Throws `ValidationError` for invalid content

### `getCard(hash)`
- Retrieves a card by its hash
- Throws `NotFoundError` if card doesn't exist

### `deleteCard(hash)`
- Deletes a card by its hash
- Returns `true` if successful
- Handles non-existent cards gracefully

### `deleteAllCards()`
- Deletes all cards in the database
- Use with caution

## Content Validation

- Maximum content length: 1,000,000 characters
- Supports various content types (strings, objects)
- Automatic content stringification
- Custom validator support

## Testing

```bash
# Run tests
npm test

# Generate coverage report
npm test -- --coverage
```

## Error Hierarchy

- `MCardError` (Base Error)
  - `ValidationError`
  - `AuthorizationError`
  - `NetworkError`
  - `NotFoundError`

## Performance Considerations

- Lightweight Axios-based implementation
- Configurable request timeout
- Minimal overhead for validation and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
