# MCard Storage Service

A standalone storage service implementation using MCard Core, FastAPI, and uvicorn. This service provides a RESTful API for storing and retrieving content-addressable data using the MCard data structure.

## Features

- RESTful API for MCard operations
- Configurable through environment variables
- Built on FastAPI and uvicorn for high performance
- Uses MCard Core's robust storage and hashing capabilities
- Supports concurrent operations
- Includes health check endpoint
- Comprehensive error handling

## Prerequisites

- Python 3.12+
- MCard Core library
- uvicorn
- python-dotenv
- fastapi

## Configuration

Create a `.env` file with the following variables:

```env
# Server Configuration
MCARD_SERVICE_HOST=0.0.0.0
MCARD_SERVICE_PORT=8000
MCARD_SERVICE_WORKERS=4
MCARD_SERVICE_LOG_LEVEL=info

# MCard Core Configuration
MCARD_API_KEY=your_api_key_here
MCARD_MANAGER_DB_PATH=MCardManagerStore.db
MCARD_MANAGER_DATA_SOURCE=sqlite
MCARD_MANAGER_POOL_SIZE=5
```

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate  # On Unix/macOS
   .venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Service

Start the service using uvicorn:

```bash
uvicorn mcard_storage_service:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use the provided start script:

```bash
./start_service.sh
```

## API Endpoints

### Health Check
- `GET /health`
  - Returns service health status
  - No authentication required

### Card Operations
- `POST /cards/`
  - Create a new card
  - Requires API key
  - Returns 201 on success

- `GET /cards/{hash}`
  - Retrieve a card by hash
  - Requires API key
  - Returns 200 on success, 404 if not found

- `GET /cards/`
  - List cards with optional filtering
  - Requires API key
  - Supports pagination and content filtering

- `DELETE /cards/{hash}`
  - Delete a card
  - Requires API key
  - Returns 204 on success

## Error Handling

The service follows standard HTTP status codes:
- 200: Success
- 201: Created
- 204: No Content (successful deletion)
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Implementation Details

This service is built on top of MCard Core's robust infrastructure:

- Uses `mcard_api.py` for core API functionality
- Leverages `config.py` for configuration management
- Implements additional health monitoring
- Adds service-specific logging
- Includes graceful shutdown handling

## Monitoring

The service provides basic monitoring through:
- Health check endpoint
- Structured logging
- Error tracking
- Basic metrics (requests, response times)

## Security

- API key authentication required for all card operations
- TLS support through uvicorn (when configured)
- Input validation and sanitization
- Rate limiting (configurable)

## Development

To run in development mode with auto-reload:

```bash
uvicorn mcard_storage_service:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Run the test suite:

```bash
pytest tests/
```

## License

Same as MCard Core
