# MonadicCards

A modern, composable card management application built with Next.js and direct integration with MCard API.

## 🏗️ Architectural Design

### Overall Architecture

The MonadicCards application follows a three-tier architectural pattern:

1. **Frontend (Next.js + React)**
   - Uses Next.js for server-side rendering and routing
   - Provides a responsive and interactive user interface
   - Manages card display and user interactions

2. **API Server (Next.js API Routes)**
   - Manages the MCard API service lifecycle
   - Handles environment configuration
   - Provides logging and monitoring

3. **MCard Backend**
   - Utilizes MCard's setup.py for consistent configuration
   - Handles core business logic and data persistence
import { spawn } from 'child_process';
import path from 'path';

interface MCardConfig {
  dbPath?: string;
  maxConnections?: number;
  timeout?: number;
  maxContentSize?: number;
  configOverrides?: Record<string, any>;
}

export class MCardService {
  private pythonProcess: any;
  private initialized: boolean = false;

  constructor(private config: MCardConfig = {}) {
    this.config = {
      dbPath: './data/monadic_cards.db',
      maxConnections: 5,
      timeout: 5.0,
      maxContentSize: 10 * 1024 * 1024, // 10MB
      ...config
    };
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    // Ensure we're using the virtual environment's Python
    const pythonPath = path.join(process.cwd(), 'mcard_venv', 'bin', 'python');
    
    // Create Python script that uses MCardSetup
    const setupScript = `
import asyncio
from mcard.infrastructure.setup import MCardSetup

async def main():
    setup = MCardSetup(
        db_path="${this.config.dbPath}",
        max_connections=${this.config.maxConnections},
        timeout=${this.config.timeout},
        max_content_size=${this.config.maxContentSize}
        ${this.config.configOverrides ? `, config_overrides=${JSON.stringify(this.config.configOverrides)}` : ''}
    )
    
    async with setup:
        # Your MCard operations here
        pass

if __name__ == "__main__":
    asyncio.run(main())
    `;

    this.pythonProcess = spawn(pythonPath, ['-c', setupScript]);
    
    return new Promise((resolve, reject) => {
      this.pythonProcess.on('error', (err: Error) => {
        console.error('Failed to start MCard service:', err);
        reject(err);
      });

      this.pythonProcess.stdout.on('data', (data: Buffer) => {
        console.log('MCard service output:', data.toString());
      });

      this.pythonProcess.stderr.on('data', (data: Buffer) => {
        console.error('MCard service error:', data.toString());
      });

      // Wait for initialization
      setTimeout(() => {
        this.initialized = true;
        resolve();
      }, 1000);
    });
  }

  async createCard(content: string): Promise<string> {
    if (!this.initialized) {
      await this.initialize();
    }
    
    // Implement card creation logic using Python bridge
    // This would involve sending commands to the Python process
    return 'card_hash';
  }

  async getCard(hash: string): Promise<any> {
    if (!this.initialized) {
      await this.initialize();
    }
    
    // Implement card retrieval logic
    return null;
  }

  async listCards(options: { 
    startTime?: Date, 
    endTime?: Date, 
    content?: string,
    limit?: number,
    offset?: number
  }): Promise<any[]> {
    if (!this.initialized) {
      await this.initialize();
    }
    
    // Implement card listing logic
    return [];
  }

  async deleteCard(hash: string): Promise<void> {
    if (!this.initialized) {
      await this.initialize();
    }
    
    // Implement card deletion logic
  }

  async cleanup(): Promise<void> {
    if (this.pythonProcess) {
      this.pythonProcess.kill();
      this.initialized = false;
    }
  }
}

// Export a singleton instance
export const mcardService = new MCardService();   - Provides RESTful API for card operations

### Key Design Principles

- **Simplicity**: Direct frontend-to-backend communication
- **Performance**: Efficient data handling with MCard's setup
- **Flexibility**: Easy to modify or replace components
- **Reliability**: Proper service lifecycle management

## 🚀 Project Structure

```text
/
├── data/               # Database and persistent storage
│   └── monadic_cards.db   # SQLite database file
├── public/
├── src/
│   ├── app/           # Next.js app directory
│   ├── components/
│   │   ├── cards/
│   │   ├── layout/
│   │   └── ui/
│   ├── config/
│   ├── lib/
│   └── styles/
└── package.json
```

## 🔨 Prerequisites

### Python Virtual Environment Setup

Before running the application, you need to set up a Python virtual environment for MCard:

```bash
# Create a Python virtual environment
python -m venv mcard_venv

# Activate the virtual environment
# On macOS/Linux:
source mcard_venv/bin/activate
# On Windows:
# .\mcard_venv\Scripts\activate

# Install MCard and its dependencies
pip install -r requirements.txt
```

Make sure to keep the virtual environment activated while running the application. The `mcard_venv` directory is already added to `.gitignore` to prevent committing virtual environment files.

## 🔧 Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PORT` | Port for the API server | `3000` |
| `MCARD_API_URL` | URL of the MCard API endpoint | `http://localhost:5000` |
| `MCARD_API_KEY` | Authentication key for MCard API | Required |
| `MCARD_MANAGER_DB_PATH` | Database file path (relative to project root) | `./data/monadic_cards.db` |
| `MCARD_MANAGER_POOL_SIZE` | Database connection pool size | `5` |
| `MCARD_MANAGER_TIMEOUT` | Database operation timeout (seconds) | `30.0` |
| `MCARD_MANAGER_MAX_CONTENT_SIZE` | Maximum content size in bytes | `10485760` |
| `MCARD_MANAGER_HASH_ALGORITHM` | Hashing algorithm for content | `sha256` |
| `MCARD_MANAGER_CUSTOM_MODULE` | Custom hashing module path | Optional |
| `MCARD_MANAGER_CUSTOM_FUNCTION` | Custom hashing function name | Optional |
| `MCARD_MANAGER_CUSTOM_HASH_LENGTH` | Custom hash length | `0` |
| `MCARD_SERVICE_LOG_LEVEL` | Logging level for the service | `INFO` |

### Data Storage

The application stores its database file in the `data` directory at the project root. This directory is automatically created when the application starts. The default database path is `./data/monadic_cards.db`.

You can customize the database location by modifying the `MCARD_MANAGER_DB_PATH` environment variable. The path should be relative to the project root directory.

## 🚀 Features

### Card Management

- **Create Cards**: Create new cards with content
- **View Cards**: View card details including content and metadata
- **List Cards**: Browse cards with advanced filtering options:
  - Filter by time range (start_time, end_time)
  - Filter by content
  - Pagination support (limit, offset)
- **Delete Cards**: Remove cards by hash

### MCard Integration

The application integrates with MCard using the official setup.py module, providing:

- **Automated Setup**: Consistent database and service configuration
- **Connection Management**: Efficient database connection pooling
- **Card Provisioning**: 
  - Centralized card management through CardProvisioningApp
  - Unified interface for all card operations
  - Content-defined chunking with collision detection
  - Configurable hashing algorithms with automatic strengthening
  - Reference card creation for duplicate content
  - Detailed event tracking for collisions and duplicates
- **Content Management**: 
  - Content-defined chunking
  - Configurable hashing algorithms
  - Automatic content type interpretation
- **Security**: 
  - API key authentication
  - Content size limits
  - Operation timeouts

### Architecture Updates

The application now follows a more structured architecture with clear separation of concerns:

1. **API Layer (`app/api/`)**
   - Next.js API routes for HTTP interface handling
   - Request validation
   - Error handling and HTTP status codes
   - API key verification

2. **Application Layer (`card_provisioning_app.py`)**
   - Core business logic
   - Card lifecycle management
   - Content deduplication
   - Hash collision handling
   - Event tracking

3. **Storage Layer**
   - Persistent storage operations
   - Connection pooling
   - Schema management
   - Transaction handling

This layered architecture ensures:
- Single point of truth for card operations
- Consistent error handling
- Proper separation of concerns
- Easy maintenance and testing

## 🧪 Testing

The project includes comprehensive test coverage for both the API layer and service layer. Tests are written using Jest and follow best practices for testing asynchronous operations and mocking external dependencies.

### Test Structure

```text
/__tests__
├── api/
│   └── cards.test.ts    # Tests for card-related API endpoints
├── api.test.ts          # General API functionality tests
└── mcard.service.test.ts # Tests for MCard service layer
```

### Test Categories

#### 1. MCard Service Tests
- **Card Creation**
  - Creates cards with auto-detected content type
  - Handles errors during card creation
  - Validates content and content type

- **Card Retrieval**
  - Retrieves cards by hash
  - Returns null for non-existent cards
  - Handles invalid hash values

- **Card Listing**
  - Lists cards with pagination
  - Supports empty result sets
  - Validates pagination parameters

- **Card Deletion**
  - Deletes existing cards
  - Handles deletion of non-existent cards
  - Returns appropriate error messages

#### 2. API Route Tests
- **GET /api/cards**
  - Lists all cards with pagination
  - Handles database errors
  - Returns appropriate status codes

- **GET /api/cards/[hash]**
  - Retrieves specific card by hash
  - Returns 404 for non-existent cards
  - Validates hash parameter

- **POST /api/cards**
  - Creates new cards
  - Validates request body
  - Handles content type detection

- **DELETE /api/cards/[hash]**
  - Deletes specific card
  - Returns appropriate status codes
  - Handles non-existent cards

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Test Environment

Tests use an in-memory database configuration to ensure:
- Fast test execution
- Isolation between test runs
- No interference with production data

### Mocking Strategy

The tests utilize Jest's mocking capabilities to:
- Mock the Python process communication
- Simulate various response scenarios
- Test error handling
- Ensure consistent test behavior

### Error Handling Coverage

Tests verify proper handling of:
- Invalid input data
- Network errors
- Database errors
- Resource not found scenarios
- Malformed requests
