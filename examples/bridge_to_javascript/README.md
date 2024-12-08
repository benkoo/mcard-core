# MCard JavaScript Bridge

A Node.js client library for interacting with the MCard Core content-addressable storage system.

## Features

- Simple and intuitive API for interacting with MCard Core
- Promise-based async/await interface
- Robust error handling with automatic retries
- Configurable pagination for large datasets
- Real server integration testing
- High test coverage (>95% statements, >90% branches)
- Comprehensive metrics tracking
- Debug mode for detailed logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcard-core.git
cd mcard-core/examples/bridge_to_javascript
```

2. Install dependencies:
```bash
npm install
```

3. Copy the .env.example file and configure it:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Usage

The library provides a simple client for interacting with the MCard Core server:

```javascript
const { MCardClient } = require('./src/client');

// Initialize client with custom configuration
const client = new MCardClient({
    apiKey: 'your_api_key',
    baseURL: 'http://localhost:5320',
    timeout: 5000,
    maxRetries: 3,
    retryDelay: 1000,
    debug: true
});

// Create a card
const card = await client.createCard({ 
    content: 'Hello, World!',
    metadata: { type: 'greeting' }
});

// Get a card by hash
const retrievedCard = await client.getCard(card.hash);

// List all cards with pagination
const cards = await client.listCards({ 
    page: 1, 
    pageSize: 10, 
    search: 'hello' 
});

// Get all cards (automatically handles pagination)
const allCards = await client.getAllCards();

// Delete a card
await client.deleteCard(card.hash);

// Delete all cards
await client.deleteCards();

// Get metrics
const metrics = client.getMetrics();
console.log('Success rate:', metrics.successfulRequests / metrics.totalRequests);
```

## Error Handling

The client includes comprehensive error handling:

- Network errors (connection refused, DNS resolution, etc.)
- HTTP errors (400, 401, 403, 404, 500, etc.)
- Rate limiting with automatic retries
- Timeout handling
- Invalid input validation

Example:
```javascript
try {
    await client.createCard('');  // Empty content
} catch (error) {
    console.error(error.message); // "422: Content is invalid"
}
```

## Recent Updates

### Error Handling Improvements (December 2024)

#### Network Error Detection
- Enhanced `isNetworkError` method in `client.js` to provide more robust network error handling
- Added null checks to prevent undefined errors during connection failures
- Improved detection of specific network error codes:
  - `ECONNABORTED`: Request timeout
  - `ECONNREFUSED`: Connection refused
  - `ENOTFOUND`: DNS lookup failed
  - `ETIMEDOUT`: Connection timeout

#### Key Changes
- Implemented comprehensive error handling to distinguish between network and HTTP errors
- Added defensive programming techniques to handle edge cases in error detection
- Improved test coverage for error handling scenarios

## Testing

The library uses Jest for testing and includes:

1. Real server integration tests (no mocks)
2. Comprehensive error handling tests
3. Edge case coverage
4. Metrics and monitoring tests

To run tests:

```bash
# Run all tests
npm test

# Run specific test file
npx jest client.consolidated.test.js

# Run with coverage
npm test -- --coverage
```

## Metrics and Monitoring

The client includes built-in metrics tracking:

- Total requests
- Successful/failed requests
- Retry attempts
- Average response time
- Request history (configurable size)

Enable debug mode for detailed logging:
```javascript
const client = new MCardClient({ debug: true });
```

## API Reference

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| apiKey | string | 'dev_key_123' | API key for authentication |
| baseURL | string | 'http://localhost:5320' | Base URL of the MCard server |
| timeout | number | 5000 | Request timeout in milliseconds |
| maxRetries | number | 3 | Maximum number of retry attempts |
| retryDelay | number | 1000 | Delay between retries in milliseconds |
| debug | boolean | false | Enable debug logging |
| maxHistorySize | number | 100 | Maximum size of request history |

### Methods

- `createCard(content)`: Create a new card
- `getCard(hash)`: Get a card by hash
- `listCards({ page, pageSize, search })`: List cards with pagination
- `getAllCards()`: Get all cards (handles pagination)
- `deleteCard(hash)`: Delete a card by hash
- `deleteCards()`: Delete all cards
- `getMetrics()`: Get client metrics
- `resetMetrics()`: Reset metrics counters
- `getRequestHistory()`: Get recent request history

## Environment Variables

Configure these in your `.env` file:

- `MCARD_API_KEY`: Your API key for authentication
- `MCARD_API_PORT`: Port number for the MCard Core server (default: 3000)
- `MCARD_DB_PATH`: Path to the SQLite database file
- `MCARD_STORE_MAX_CONNECTIONS`: Maximum number of concurrent database connections
- `MCARD_STORE_TIMEOUT`: Database operation timeout in seconds
- `MCARD_HASH_ALGORITHM`: Hash algorithm to use (default: sha256)

## Architecture Overview

### Core Components

1. **client.js**
   - Main JavaScript client implementation
   - Provides Promise-based API for MCard operations
   - Features:
     - Automatic error handling and retries
     - Configurable timeouts
     - Custom headers and authentication
     - Response validation
     - Type checking

2. **server.py**
   - FastAPI-based Python server
   - Implements RESTful API endpoints:
     - `/cards` - CRUD operations for cards
     - `/health` - Server health check
   - Features:
     - API key authentication
     - Request validation
     - Error handling
     - CORS support

3. **setup.py**
   - Handles Python environment setup
   - Database initialization
   - Configuration management

4. **types.ts**
   - TypeScript type definitions
   - Ensures type safety for JavaScript/TypeScript clients

## Test Structure

### Test Categories

1. **Initialization Tests** (`initialization.test.js`)
   - Client initialization
   - Configuration validation
   - API key handling
   - URL and base path handling

2. **Basic Operations** (`basic-operations.test.js`)
   - CRUD operations for cards
   - Basic functionality testing

3. **Content Types** (`content-types.test.js`)
   - Various content type handling
   - Edge cases (null, undefined, circular references)
   - Special characters
   - Large content

4. **Validation** (`validation.test.js`)
   - Input validation
   - Response validation
   - Error message validation
   - Schema validation

5. **Error Handling** (`error-handling.test.js`)
   - Network errors
   - Timeout handling
   - Server errors
   - Client errors
   - Recovery scenarios

6. **Concurrency** (`concurrency.test.js`)
   - Parallel operations
   - Race condition handling
   - Connection pooling

7. **Performance** (`performance.test.js`)
   - Load testing
   - Response time benchmarks
   - Memory usage

8. **Utils** (`utils.test.js`)
   - Helper function testing
   - Utility method validation

### Test Coverage

The test suite aims for comprehensive coverage:
- Statements: >90%
- Branches: >90%
- Functions: >90%
- Lines: >90%

## Recent Changes

### December 2024
- Automated server management in tests - Python server now starts and stops automatically during test execution
- Simplified binary content tests to focus on core functionality
- Added comprehensive mixed content testing (binary and text)
- Improved test coverage across all operations
- Enhanced error handling and retry mechanisms
- Added metrics and monitoring capabilities

## Running Tests

The test suite now automatically manages the Python server:

```bash
npm test
```

This command will:
1. Automatically start the Python server
2. Run all tests
3. Shut down the server after tests complete

Note: The manual server startup script (`start-server.sh`) is no longer needed for testing.

### Test Coverage

The current test coverage is:
- Statements: 94.32%
- Branches: 88.65%
- Functions: 100%
- Lines: 94.2%

The test suite includes:
- Basic CRUD operations
- Text content handling
- Binary content handling
- Mixed content operations
- Error handling and retries
- Search and pagination
- Metrics and monitoring

## Web Framework Integration

### Astro Integration

#### Setup

1. **Install Dependencies**
   ```bash
   # Create new Astro project
   npm create astro@latest my-mcard-app
   cd my-mcard-app

   # Install MCard client
   npm install mcard-js-bridge
   ```

2. **Environment Configuration**
   ```bash
   # Create .env file
   touch .env

   # Add MCard configuration
   MCARD_API_KEY=your_api_key
   MCARD_API_PORT=5320
   PUBLIC_MCARD_BASE_URL=http://localhost:5320
   ```

3. **Server Setup**
   ```bash
   # Create Python virtual environment in your Astro project
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

   # Start the MCard server
   python src/server.py
   ```

#### Usage Examples

1. **API Routes** (`src/pages/api/cards.ts`)
   ```typescript
   import type { APIRoute } from 'astro';
   import { MCardClient } from 'mcard-js-bridge';

   const client = new MCardClient({
     apiKey: import.meta.env.MCARD_API_KEY,
     baseUrl: import.meta.env.PUBLIC_MCARD_BASE_URL
   });

   export const GET: APIRoute = async ({ params }) => {
     try {
       const cards = await client.listCards();
       return new Response(JSON.stringify(cards), {
         status: 200,
         headers: { 'Content-Type': 'application/json' }
       });
     } catch (error) {
       return new Response(JSON.stringify({ error: error.message }), {
         status: 500,
         headers: { 'Content-Type': 'application/json' }
       });
     }
   };

   export const POST: APIRoute = async ({ request }) => {
     try {
       const body = await request.json();
       const card = await client.createCard({ content: body.content });
       return new Response(JSON.stringify(card), {
         status: 201,
         headers: { 'Content-Type': 'application/json' }
       });
     } catch (error) {
       return new Response(JSON.stringify({ error: error.message }), {
         status: 500,
         headers: { 'Content-Type': 'application/json' }
       });
     }
   };
   ```

2. **React/Preact Components** (`src/components/CardList.tsx`)
   ```typescript
   import { useState, useEffect } from 'react';
   import { MCardClient } from 'mcard-js-bridge';

   export default function CardList() {
     const [cards, setCards] = useState([]);
     const [loading, setLoading] = useState(true);
     const [error, setError] = useState(null);

     useEffect(() => {
       const fetchCards = async () => {
         try {
           const response = await fetch('/api/cards');
           const data = await response.json();
           setCards(data);
         } catch (err) {
           setError(err.message);
         } finally {
           setLoading(false);
         }
       };

       fetchCards();
     }, []);

     if (loading) return <div>Loading...</div>;
     if (error) return <div>Error: {error}</div>;

     return (
       <div>
         <h2>Stored Cards</h2>
         <ul>
           {cards.map(card => (
             <li key={card.hash}>
               <pre>{JSON.stringify(card.content, null, 2)}</pre>
             </li>
           ))}
         </ul>
       </div>
     );
   }
   ```

3. **Astro Pages** (`src/pages/index.astro`)
   ```astro
   ---
   import CardList from '../components/CardList';
   import CardForm from '../components/CardForm';
   ---

   <html>
     <head>
       <title>MCard Storage App</title>
     </head>
     <body>
       <h1>MCard Storage System</h1>
       <CardForm client:load />
       <CardList client:load />
     </body>
   </html>
   ```

4. **Form Component** (`src/components/CardForm.tsx`)
   ```typescript
   import { useState } from 'react';

   export default function CardForm() {
     const [content, setContent] = useState('');
     const [status, setStatus] = useState('');

     const handleSubmit = async (e) => {
       e.preventDefault();
       try {
         const response = await fetch('/api/cards', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ content })
         });
         const data = await response.json();
         setStatus('Card created successfully!');
         setContent('');
       } catch (error) {
         setStatus(`Error: ${error.message}`);
       }
     };

     return (
       <form onSubmit={handleSubmit}>
         <textarea
           value={content}
           onChange={(e) => setContent(e.target.value)}
           placeholder="Enter card content..."
         />
         <button type="submit">Create Card</button>
         {status && <p>{status}</p>}
       </form>
     );
   }
   ```

#### Development Workflow

1. **Start Development Environment**
   ```bash
   # Terminal 1: Start MCard server
   source .venv/bin/activate
   python src/server.py

   # Terminal 2: Start Astro dev server
   npm run dev
   ```

2. **Production Deployment**
   ```bash
   # Build Astro application
   npm run build

   # Start production servers
   # Terminal 1: Start MCard server
   python src/server.py

   # Terminal 2: Start Node server
   node dist/server/entry.mjs
   ```

#### Best Practices

1. **Error Handling**
   - Implement proper error boundaries in React components
   - Use try-catch blocks in API routes
   - Display user-friendly error messages

2. **Performance**
   - Use server-side rendering for initial card list
   - Implement pagination for large card lists
   - Cache frequently accessed cards

3. **Security**
   - Store API keys in environment variables
   - Implement rate limiting
   - Validate input on both client and server

4. **TypeScript Integration**
   - Use provided TypeScript definitions
   - Enable strict mode
   - Create custom type guards

#### Advanced Features

1. **Real-time Updates**
   ```typescript
   // Using Server-Sent Events
   export const GET: APIRoute = async ({ request }) => {
     return new Response(new ReadableStream({
       async start(controller) {
         const client = new MCardClient();
         
         setInterval(async () => {
           const cards = await client.listCards();
           controller.enqueue(`data: ${JSON.stringify(cards)}\n\n`);
         }, 1000);
       }
     }), {
       headers: {
         'Content-Type': 'text/event-stream',
         'Cache-Control': 'no-cache',
         'Connection': 'keep-alive'
       }
     });
   };
   ```

2. **File Upload Support**
   ```typescript
   // Component for handling file uploads
   export default function FileUpload() {
     const handleUpload = async (file) => {
       const reader = new FileReader();
       reader.onload = async (e) => {
         const content = e.target.result;
         await fetch('/api/cards', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ content })
         });
       };
       reader.readAsText(file);
     };

     return (
       <input 
         type="file" 
         onChange={(e) => handleUpload(e.target.files[0])} 
       />
     );
   };
   ```

This integration guide demonstrates how to use the MCard JavaScript client and Python server in a modern Astro web application, including setup, basic usage, and advanced features.

## Contributing
1. Fork the repository
2. Create your feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License
MIT License

## Development

### Running Tests

```bash
npm test
```

### Code Formatting

```bash
npm run format
```

### Linting

```bash
npm run lint

```
