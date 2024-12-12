# MCardClient Test Suite

This directory contains a comprehensive test suite for the MCardClient JavaScript library. The tests are organized into multiple files, each focusing on specific aspects of the client's functionality.

## Test Files Organization

### Core Functionality
- `client.test.js` - Core CRUD operations and basic functionality
- `initialization.test.js` - Client initialization and configuration tests

### Feature-Specific Tests
- `basic-operations.test.js` - Basic card operations (create, read, update, delete)
- `content-types.test.js` - Tests for different content types and edge cases
- `validation.test.js` - Input validation and boundary condition tests

### Advanced Tests
- `error-handling.test.js` - Error handling and recovery scenarios
- `concurrency.test.js` - Concurrent operations and race conditions
- `performance.test.js` - Performance and load testing

### Utilities
- `utils.test.js` - Utility function tests
- `utils/test-setup.js` - Shared test setup utilities

## Running Tests

### Running All Tests
To run the complete test suite in the recommended order:
```bash
node tests/run-tests.js
```

### Running Individual Test Files
To run a specific test file:
```bash
npx jest tests/[filename].test.js
```

For example:
```bash
npx jest tests/client.test.js
```

### Running Tests with Watch Mode
For development, you can run tests in watch mode:
```bash
npx jest --watch tests/[filename].test.js
```

## Test Utilities

The `utils/test-setup.js` file provides several utility functions to help with testing:

- `createTestClient()` - Creates a test client with default configuration
- `createInvalidClient()` - Creates a client with invalid credentials for error testing
- `cleanupCards()` - Cleans up all cards for a client
- `createTestDirectory()` - Creates a temporary test directory
- `cleanupTestDirectory()` - Cleans up test directories and files
- `createSampleFiles()` - Creates sample files for content type testing
- `createMockAxios()` - Creates a mock axios instance for network testing
- `setupMockAxios()` - Sets up mock axios for a client

## Test Configuration

The test suite uses a centralized configuration system in `config/test-config.js`. This configuration includes:

### Client Configuration
- Default and invalid client settings
- API endpoints and credentials

### Test Data Configuration
- Sample content of various types and sizes
- Test directory locations
- Content size thresholds

### Performance Settings
- Concurrent operation limits
- Rate limiting parameters
- Timeout values

### Network Configuration
- Timeout settings
- Retry attempts and delays
- Error simulation settings

### Test Suite Settings
- Test timeouts for different categories
- Cleanup configuration
- Test execution order

## Using the Configuration

Access the configuration in your tests:

```javascript
const { config } = require('./utils/test-setup');

// Use configuration values
const { contentSizes } = config.testData;
const largeContent = 'x'.repeat(contentSizes.large);
```

### Utility Functions

The configuration also provides utility functions:

```javascript
const { utils } = config;

// Generate random test data
const randomString = utils.generateRandomString(20);
const binaryData = utils.generateRandomBinary(1024);

// Format sizes
const formatted = utils.formatBytes(1024 * 1024); // "1 MB"

// Add delays in tests
await utils.delay(1000); // Wait for 1 second

## Test Categories

### 1. Core Functionality Tests
- Basic CRUD operations
- Health check functionality
- Basic error cases

### 2. Content Type Tests
- Text content
- Binary data
- Images
- JSON data
- Special characters
- Unicode support

### 3. Concurrency Tests
- Parallel operations
- Race conditions
- Load testing
- Request bursts

### 4. Validation Tests
- Input validation
- Boundary conditions
- Edge cases
- Parameter validation

### 5. Error Handling Tests
- Network errors
- Invalid credentials
- Missing parameters
- Server errors
- Timeout handling

## Contributing

When adding new tests:

1. Choose the appropriate test file based on the functionality being tested
2. Use the provided test utilities from `test-setup.js`
3. Follow the existing test structure and naming conventions
4. Add any new utility functions to `test-setup.js` if needed
5. Update this README if adding new test categories or utilities

## Best Practices

1. Each test should be independent and not rely on the state from other tests
2. Use `beforeEach` to clean up any resources created during tests
3. Mock external dependencies when testing error conditions
4. Use descriptive test names that explain the scenario being tested
5. Group related tests using `describe` blocks
6. Add comments for complex test scenarios
