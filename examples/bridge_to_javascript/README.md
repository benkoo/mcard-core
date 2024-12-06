# MCard JavaScript Bridge

A FastAPI-based server that provides a RESTful API for the MCard storage system, designed to be used as a bridge for JavaScript applications.

## Features

- RESTful API endpoints for card operations (create, read, delete, list)
- API key authentication for secure access
- Robust error handling and validation
- Comprehensive test suite
- CORS support for browser-based applications

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcard-core/examples/bridge_to_javascript
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following configuration:
```env
MCARD_API_KEY=your_secure_api_key
MCARD_API_PORT=8000
MCARD_STORE_PATH=./data/mcard.db
MCARD_STORE_MAX_CONNECTIONS=5
MCARD_STORE_TIMEOUT=5.0
```

## Usage

1. Start the server:
```bash
python src/server.py
```

2. The server will be available at `http://localhost:8000` (or the port specified in your `.env` file)

3. Use the following API endpoints:

### API Endpoints

All endpoints require the `X-API-Key` header with your API key.

#### Health Check
- `GET /health`
- Returns server health status
- Response: `{"status": "healthy"}`

#### Create Card
- `POST /cards`
- Request body: `{"content": "Your card content"}`
- Response: Card object with content, hash, and timestamp

#### Get Card
- `GET /cards/{hash}`
- Returns a specific card by its hash
- Response: Card object with content, hash, and timestamp

#### List Cards
- `GET /cards`
- Returns a list of all cards
- Response: Array of card objects

#### Delete Card
- `DELETE /cards/{hash}`
- Deletes a specific card by its hash
- Response: `{"status": "success"}`

### Response Models

Card Response Object:
```json
{
  "content": "string",
  "hash": "string",
  "g_time": "string (ISO format)"
}
```

## Development

### Project Structure

```
bridge_to_javascript/
├── src/
│   ├── __init__.py
│   └── server.py
├── tests/
│   └── test_server.py
├── .env
├── requirements.txt
└── README.md
```

### Running Tests

Run the test suite using pytest:

```bash
pytest -v tests/test_server.py
```

The test suite includes:
- API key validation
- CRUD operations for cards
- Error handling scenarios
- Edge cases (empty content, missing fields, etc.)

### Environment Variables

- `MCARD_API_KEY`: API key for authentication
- `MCARD_API_PORT`: Port for the FastAPI server
- `MCARD_STORE_PATH`: Path to the SQLite database file
- `MCARD_STORE_MAX_CONNECTIONS`: Maximum database connections
- `MCARD_STORE_TIMEOUT`: Database operation timeout in seconds

### Error Handling

The API implements proper error handling with appropriate HTTP status codes:
- 200: Successful operation
- 400: Bad request (invalid input)
- 401: Unauthorized (invalid API key)
- 404: Resource not found
- 422: Validation error (missing required fields)
- 500: Internal server error

## Security

- API key authentication is required for all endpoints
- CORS middleware is configured to allow cross-origin requests
- Environment variables are used for sensitive configuration
- Database connections are properly managed and cleaned up

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

[Your License Here]
