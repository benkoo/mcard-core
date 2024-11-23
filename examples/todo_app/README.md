# MCard Todo App

A simple Todo application that demonstrates the usage of MCard as a backend for storing and managing todo items. This example showcases MCard's content-addressable storage capabilities and proper integration with Flask's application context.

## Features

- Create new todos with title and optional description
- Mark todos as complete/incomplete
- Delete todos
- View creation and update timestamps
- Clean and responsive UI using Tailwind CSS
- Thread-safe database operations
- Proper transaction management
- Comprehensive error handling and logging

## Setup

1. Make sure you have Python 3.7+ installed
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   flask --app app run --port 5002 --debug
   ```
4. Open your browser and navigate to `http://localhost:5002`

## Implementation Details

The application demonstrates best practices for using MCard in a web application:

### Technology Stack
- Flask for the web framework
- MCard for content-addressable storage
- SQLite as the underlying database (via MCard)
- Tailwind CSS for styling

### Database Management
- Uses Flask's application context (`g`) for thread-safe database connections
- Proper connection lifecycle management (creation and cleanup)
- Transaction management with commit/rollback support
- Automatic database initialization and directory creation

### Data Structure
Each todo item is stored as an MCard with the following structure:
```json
{
    "title": "Todo title",
    "description": "Optional description",
    "done": false,
    "created_at": "ISO timestamp",
    "updated_at": "ISO timestamp"
}
```

### Key Components
- `get_storage()`: Provides thread-local MCardStorage instances
- `get_collection()`: Manages thread-local MCardCollection instances
- `teardown_db()`: Ensures proper cleanup of database connections
- Comprehensive error handling and debug logging throughout

### Best Practices Demonstrated
1. **Thread Safety**
   - Per-request database connections
   - Proper connection lifecycle management
   - Safe concurrent access to the database

2. **Error Handling**
   - Comprehensive try/except blocks
   - Transaction management
   - Detailed error logging
   - Proper cleanup on errors

3. **Data Integrity**
   - Automatic content hash generation
   - Transaction-based updates
   - Proper timestamp handling
   - Content verification

4. **Code Organization**
   - Clear separation of concerns
   - Modular function design
   - Consistent error handling patterns
   - Comprehensive logging

## Development

To run the application in development mode with debug logging:
```bash
flask --app app run --port 5002 --debug
```

The debug mode provides detailed logging of:
- Database operations
- Card creation and updates
- Transaction management
- Error conditions

## Troubleshooting

Common issues and solutions:

1. **Database Permissions**: Ensure the application has write permissions to the database directory
2. **Port Conflicts**: If port 5002 is in use, specify a different port using `--port`
3. **Database Locks**: The application properly handles SQLite locks, but if issues occur, check for lingering connections
4. **Thread Errors**: If you see thread-related errors, ensure you're using the latest version with thread-safe connections
