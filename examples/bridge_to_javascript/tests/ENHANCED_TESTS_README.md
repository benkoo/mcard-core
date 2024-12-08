# Enhanced MCard Client Tests

## Overview

This test suite comprehensively validates the functionality of the Enhanced MCard JavaScript Client. It covers various aspects of the client's behavior, including:

- Error Handling
- Content Validation
- Metrics Tracking
- Logging
- Configuration
- Card Operations

## Test Categories

### 1. Error Handling Tests
- Validates custom error classes
- Checks error type and status code
- Ensures appropriate errors are thrown for different scenarios

### 2. Content Validation Tests
- Verifies content length restrictions
- Supports custom validation rules
- Prevents invalid content creation

### 3. Metrics Tracking Tests
- Tracks successful and failed requests
- Monitors error types
- Provides reset functionality for metrics

### 4. Logging Tests
- Verifies debug logging
- Checks log level functionality
- Ensures logging doesn't interfere with operations

### 5. Configuration Tests
- Validates client configuration options
- Checks default and custom configurations
- Ensures flexibility in client setup

### 6. Card Operations Tests
- Tests card creation
- Validates card retrieval
- Checks card deletion

## Running Tests

```bash
# Run all tests
npm test

# Run only enhanced client tests
npm run test:enhanced

# Generate coverage report
npm run test:coverage
```

## Best Practices

1. Use mock adapters for network requests
2. Test both successful and failure scenarios
3. Verify error handling and metrics
4. Check configuration flexibility

## Dependencies

- Jest
- Axios Mock Adapter
- Custom Error Classes
- Metrics Tracking System

## Continuous Integration

These tests are designed to be run in CI/CD pipelines to ensure the reliability of the MCard JavaScript Client.
