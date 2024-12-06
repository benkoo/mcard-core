# MCard JavaScript Bridge Server

A robust FastAPI-based server that provides a bridge between JavaScript applications and the MCard system, enabling efficient card creation, retrieval, and management through a RESTful API interface.

## Features

- **RESTful API Endpoints**
  - Create cards with various content types (text, HTML, JavaScript, SQL, binary)
  - Retrieve cards by hash
  - List all cards
  - Delete cards
  - Health check endpoint

- **Security**
  - API key authentication
  - Request validation
  - Error handling

- **Performance Optimizations**
  - Batch processing for large-scale operations
  - Connection pooling
  - Configurable timeouts and retries
  - Adaptive delays for system stability

## Requirements

- Python 3.12 or higher
- FastAPI
- SQLite database
- Additional dependencies in `requirements.txt`

## Environment Variables

```bash
MCARD_API_KEY=your_api_key
MCARD_STORE_PATH=path_to_database
MCARD_STORE_MAX_CONNECTIONS=20
MCARD_STORE_TIMEOUT=30.0
```

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (see above)

## Testing Framework

The project includes a comprehensive test suite that verifies:

### Basic Operations
- API key validation
- Card CRUD operations
- Error handling

### Content Type Support
- HTML content
- JavaScript code
- SQL queries
- Mixed content
- Base64 encoded images
- Binary data
- Large binary content

### Performance and Reliability
- Batch processing (100 cards in groups of 10)
- Concurrent operations
- Error recovery with retries
- System stability under load

### Test Configuration
- Increased database connections (20)
- Extended timeouts (30 seconds)
- Adaptive delays between operations
- Comprehensive error logging

## Running Tests

Run all tests:
```bash
pytest -v tests/test_server.py
```

Run specific test:
```bash
pytest -v tests/test_server.py::test_name
```

## Performance Considerations

The server implements several strategies to handle high-load scenarios:

1. **Batch Processing**
   - Operations are processed in configurable batch sizes
   - Default batch size: 10 items
   - Automatic delays between batches

2. **Error Handling**
   - Retry mechanism for failed operations
   - Exponential backoff
   - Detailed error logging

3. **Database Optimization**
   - Connection pooling
   - Configurable timeouts
   - Transaction management

4. **System Stability**
   - Adaptive delays based on success rates
   - System recovery periods
   - Resource monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes with descriptive messages
4. Push to your branch
5. Create a Pull Request

## License

This project is part of the MCard Core system. See the LICENSE file for details.
