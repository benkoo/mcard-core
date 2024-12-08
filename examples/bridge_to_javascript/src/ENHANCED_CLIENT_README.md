# Enhanced MCard JavaScript Client

## Key Improvements

### 1. Advanced Error Handling
- Custom error classes for different error types:
  - `MCardError`: Base error class
  - `NetworkError`: Network-related errors
  - `ValidationError`: Content validation errors
  - `AuthorizationError`: Authentication issues
  - `NotFoundError`: Resource not found errors

### 2. Comprehensive Metrics Tracking
- Detailed metrics collection
- Configurable request history
- Error type tracking
- Average response time calculation

### 3. Flexible Configuration
- Configuration builder pattern
- Easy client initialization
- Configurable logging and metrics

### 4. Enhanced Logging
- Timestamped logs
- Log level support
- Detailed request/response logging

### 5. Robust Content Validation
- Flexible validation options
- Custom validator support
- Safe object stringification

## Usage Example

```javascript
const { 
    EnhancedMCardClient, 
    Logger 
} = require('./enhanced-client');

// Create client with advanced configuration
const client = new EnhancedMCardClient({
    baseURL: 'http://localhost:5320',
    apiKey: 'your-api-key',
    timeout: 3000,
    debug: true  // Enables detailed logging
});

try {
    // Create a card with validation
    const card = await client.createCard('Hello, World!', {
        type: 'greeting'
    });

    // Get metrics
    const metrics = client.getMetrics();
    console.log(metrics);
} catch (error) {
    // Detailed error handling
    if (error instanceof ValidationError) {
        console.error('Validation failed:', error.message);
    }
}
```

## Configuration Options

- `baseURL`: Server base URL
- `apiKey`: Authentication key
- `timeout`: Request timeout
- `debug`: Enable debug logging

## Error Handling

Different error types provide more context:
- `error.type`: Error category
- `error.status`: HTTP status code
- `error.originalError`: Original error object

## Metrics Tracking

Metrics include:
- Total requests
- Successful/failed requests
- Average response time
- Detailed error breakdown
- Request history

## Best Practices

1. Use configuration builder for flexible setup
2. Leverage custom error types
3. Monitor metrics
4. Use logging for debugging

## Performance Considerations

- Minimal overhead
- Configurable metrics history
- Efficient error handling
