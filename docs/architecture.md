# MCard Architecture

## Overview
MCard is a content-addressable storage system designed with a clean, layered architecture. The system is built to be database-agnostic, allowing for different storage backends while maintaining a consistent API.

## Core Components

### Domain Layer
- `MCard`: Core model representing a stored card
  - Content storage with automatic hash computation
  - Immutable hash and timestamp properties
  - Support for both text and binary content

### Application Layer
- `CardService`: Business logic for card operations
  - Card creation and retrieval
  - Content validation and hash computation
  - Time-based operations

### Infrastructure Layer

#### Persistence
- `AsyncPersistenceWrapper`: Main persistence abstraction
  - Database-agnostic interface
  - Implements `CardStore` protocol
  - Handles all database operations

- `BaseStore`: Abstract base class for database engines
  - Defines standard interface for all engines
  - Provides common functionality
  - Ensures consistent behavior across engines

- Engine-Specific Implementations:
  - `SQLiteStore`: SQLite implementation
    - Inherits from `BaseStore`
    - Handles SQLite-specific operations
    - Manages database connections and transactions

#### Setup and Configuration
- `MCardSetup`: Centralized setup functionality
  - Database configuration and initialization
  - Engine selection and configuration
  - Content interpreter setup
  - Resource management

### Interface Layer
- API Interface
  - RESTful endpoints for card operations
  - Consistent error handling
  - Clear request/response contracts

- CLI Interface
  - Command-line tools for card operations
  - Interactive demo functionality
  - Batch operation support

## Database Schema
The system uses a deliberately simple, single-table design:

### Card Table
```sql
CREATE TABLE card (
    hash TEXT PRIMARY KEY,  -- Unique identifier
    content BLOB,           -- Card content
    g_time TEXT            -- Global timestamp
);
CREATE INDEX idx_card_g_time ON card(g_time);
```

This design was chosen for:
- Simplicity and maintainability
- Efficient querying
- Minimal data redundancy
- Easy backup and restoration

## Key Features

### Content Addressing
- Automatic hash computation for all content
- SHA-512 hash algorithm
- Collision detection and handling
- Content deduplication

### Time Management
- UTC timestamps for all operations
- ISO 8601 format with timezone
- Time-based querying and filtering

### Extensibility
- Database-agnostic design
- Plugin architecture for new engines
- Configurable components
- Clear extension points

## Testing Strategy
- Comprehensive test coverage
- Unit tests for all components
- Integration tests for database operations
- Performance testing for critical paths
- Mock-based testing for external dependencies

## Configuration
The system supports various configuration options:
- Database selection and configuration
- Connection pooling and timeouts
- Content size limits
- Hash algorithm selection
- Custom overrides for specific needs

## Future Considerations
- Additional database engine support
- Enhanced search capabilities
- Improved content type handling
- Performance optimizations
- Clustering support
