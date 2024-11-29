# MCard Core

A Python library implementing an algebraically closed data structure for content-addressable storage. MCard ensures that every piece of content in the system is uniquely identified by its hash and temporally ordered by its claim time, enabling robust content verification and precedence ordering.

## Core Concepts

MCard implements an algebraically closed system where:
1. Every MCard is uniquely identified by its content hash (configurable, defaulting to SHA-256)
2. Every MCard has an associated claim time (timezone-aware timestamp with microsecond precision)
3. The database maintains these invariants automatically
4. Content integrity is guaranteed through immutable hashes
5. Temporal ordering is preserved at microsecond precision

This design provides several key guarantees:
- **Content Integrity**: The content hash serves as both identifier and verification mechanism
- **Temporal Signature**: All cards are associated with a timestamp: `g_time`
- **Precedence Verification**: The claim time enables determination of content presentation order
- **Algebraic Closure**: Any operation on MCards produces results that maintain these properties
- **Type Safety**: Built on Pydantic with strict validation and type checking

Each MCard has three fundamental properties:
- `content`: The actual data being stored (string or bytes)
- `hash`: A cryptographic hash of the content, using SHA-256 by default (configurable to other algorithms)
- `g_time`: A timezone-aware timestamp with microsecond precision, representing the global time when the card was claimed

The `hash` is calculated using SHA-256 by default but can be configured to use different cryptographic hash functions through the `HashingSettings`. This flexibility allows you to choose the hash algorithm that best suits your security and performance requirements.

The `g_time` (global time) is a crucial concept in MCard that ensures consistent temporal ordering across different timezones and systems. It represents the moment when a card is claimed in the global timeline, with microsecond precision (e.g., "2024-01-24 15:30:45.123456+00:00"), making it possible to establish clear and precise precedence relationships between cards regardless of where they were created.

## MCard Data Structure

The `MCard` class is a simple data structure designed to encapsulate content-addressable data. It consists of three tightly coupled fields:

- `content`: The actual content of the MCard, which can be a string or bytes.
- `hash`: A SHA-256 hash of the content, computed at initialization. The hash computation is configurable and extensible, allowing for different cryptographic hash functions to be used as needed.
- `g_time`: The timestamp when the hash was computed, recorded with local timezone information and microsecond precision, stored as a string.

The `MCard` class is designed to operate independently of third-party libraries, utilizing Python's built-in `hashlib` for hashing and `datetime` for time handling.

## Theoretical Foundation

MCard's design is rooted in Category Theory, where:
- Each MCard represents a morphism (a mapping between objects)
- Compositions of MCards form functors (structure-preserving mappings)
- Transformations between MCards are natural transformations

This aligns with Lambda Calculus's three fundamental abstractions:
1. **Alpha Abstraction**: Variable renaming/substitution
   - In MCard: Content transformation with preserved semantics
2. **Beta Abstraction**: Function application
   - In MCard: Applying transformations to content
3. **Eta Abstraction**: Function equivalence
   - In MCard: Different paths yielding equivalent results

Like HyperCard and HyperTalk before it, MCard aims to be a general-purpose programming system. However, it does so with a stronger theoretical bend that enables:
- Formal verification of transformations
- Guaranteed composition properties
- Traceable data lineage
- Pure functional transformations

## Features

### Core MCard Attributes
- `content`: The actual content data (supports strings, bytes, and arbitrary types)
- `hash`: A cryptographic hash of the content, using SHA-256 by default (configurable to other algorithms)
- `g_time`: A timezone-aware timestamp with microsecond precision

### Hash Collision Protection
- Comprehensive test suite for detecting and handling hash collisions
- Automated switching to stronger hashing algorithms when potential collisions are detected
- Configurable hash algorithm selection through `HashingSettings`
- Built-in safeguards to maintain data integrity
- Collision-aware hashing service with progressive algorithm strengthening (MD5 → SHA1 → SHA256 → SHA512)
- Async support for repository-based collision detection

### Storage Features
- SQLite-based persistent storage with connection pooling
- Binary content support with automatic text/binary detection
- Efficient batch operations for saving, retrieving, and deleting
- Transaction management with nested transaction support using SQLite savepoints
- Automatic rollback on errors
- Thread-safe connection management
- Time-based query support with timezone awareness
- Pagination for large result sets

### Time Management
- Configurable timezone support
- UTC and local time handling
- Custom time and date formats
- Time range operations
- Timezone conversion utilities
- Time comparison and validation functions

### Collection Management
- Automatic temporal ordering
- Time range queries
- Copy-on-read pattern for thread safety
- Efficient in-memory sorting
- Real-time collection refresh capability

## Repository Management

To ensure consistent data persistence and avoid errors, it is crucial that the repository operates as a single instance throughout the application lifecycle. This is particularly important during testing or any runtime operations. If multiple instances are created, it can lead to separate data pools, causing confusion and potential errors in data retrieval and manipulation.

### Key Points:
- **Singleton Repository**: The repository should be instantiated as a singleton to maintain a single source of truth for all operations.
- **Data Consistency**: A single repository instance ensures that all data operations are consistent and reflect the current state of the database.
- **Avoiding Confusion**: Multiple instances can lead to fragmented data pools, making it difficult to track and manage data effectively.

Ensure that your application or testing setup maintains a single repository instance to leverage the full benefits of MCard's robust data management capabilities.

## API Response Codes

The API uses standard HTTP response codes to indicate the success or failure of requests:

### Success Codes
- **201 Created**: Successfully created a new card
- **204 No Content**: Successfully deleted a card
- **200 OK**: Successfully retrieved card(s)

### Client Error Codes
- **400 Bad Request**: Invalid request parameters or content
- **401 Unauthorized**: Missing or invalid API key
- **404 Not Found**: Requested card does not exist

### Server Error Codes
- **500 Internal Server Error**: Unexpected server-side error

All error responses include a detail message to help diagnose the issue.

## Dependencies

The project relies on several key dependencies:
- `python-dateutil`
- `SQLAlchemy`
- `pydantic`
- `aiosqlite`
- `pytest` and `pytest-asyncio` for testing

## Installation

To set up the project, follow these steps:

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - On macOS and Linux:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Testing

The MCard Core library includes a comprehensive test suite organized into several key areas:

### Test Structure

```
tests/
├── application/          # Application service layer tests
├── domain/              # Domain model and service tests
│   ├── models/          # Core model tests (MCard, exceptions, etc.)
│   └── services/        # Domain service tests (hashing, time)
├── infrastructure/      # Infrastructure layer tests
│   ├── content/         # Content type detection tests
│   └── persistence/     # SQLite persistence tests
└── interfaces/          # Interface layer tests
    └── cli/            # CLI interface tests
```

### Key Test Areas

1. **Domain Model Tests**
   - MCard creation with various content types
   - Hash generation and validation
   - Time-based operations and ordering
   - Exception handling and validation
   - Configuration management

2. **Persistence Layer Tests**
   - Basic CRUD operations
   - Transaction management and isolation
   - Concurrent operations handling
   - Batch operations and pagination
   - Content type handling (binary/text)
   - Connection pool management
   - Performance benchmarking
   - Storage error propagation
   - Race condition prevention

3. **Content Handling Tests**
   - Binary vs text content detection
   - MIME type detection
   - XML and JSON validation
   - Content size validation

4. **Service Layer Tests**
   - Card service operations
   - Collision-aware hashing
   - Custom hash function support
   - Time service operations

5. **API Interface Tests**
   - HTTP status code validation (201 for creation, 204 for deletion)
   - Error response handling (404 for not found, 500 for server errors)
   - Content filtering with case-insensitive matching
   - API key authentication
   - Request validation
   - Response format verification

6. **CLI Interface Tests**
   - Command execution
   - Error handling
   - Input validation

### Test Features

- **Automated Fixtures**: Uses pytest fixtures for database setup/teardown
- **Comprehensive Coverage**: Over 140 test cases covering all major components
- **Concurrent Testing**: Validates thread-safety and transaction isolation
- **Error Simulation**: Tests error handling and recovery mechanisms
- **Performance Metrics**: Includes benchmarks for key operations

### Running Tests

To run the test suite:

```bash
pytest tests/
```

For verbose output with logging:

```bash
pytest -v tests/ --log-cli-level=DEBUG
```

To run specific test categories:

```bash
pytest tests/domain/          # Run domain tests only
pytest tests/infrastructure/  # Run infrastructure tests only
pytest tests/interfaces/      # Run interface tests only
```

## Configuration System

MCard Core uses a robust configuration management system that provides flexible, environment-aware settings with strong validation. The configuration system is designed with the following principles:

### Key Features

- **Environment-Based Configuration**: Supports multiple configuration sources:
  - Default configuration for standard deployments
  - Environment variables for runtime configuration
  - `.env` files for development settings
  - Special test configuration for isolated testing

- **Hierarchical Override System**:
  1. Environment variables (highest priority)
  2. `.env` file settings
  3. Default configuration values (lowest priority)

- **Validation and Type Safety**:
  - Strict validation of all configuration values
  - Type checking for numeric parameters
  - Range validation for connection limits and timeouts
  - Hash algorithm validation with support for custom implementations

### Configuration Components

#### Repository Configuration
- `db_path`: Database file location (defaults to `data/mcard.db`)
- `max_connections`: Maximum concurrent database connections (default: 5)
- `timeout`: Connection timeout in seconds (default: 30.0)

#### Hashing Configuration
- `algorithm`: Hash algorithm selection (default: "sha256")
  - Supported algorithms: md5, sha1, sha224, sha256, sha384, sha512
  - Custom algorithm support with module/function specification
- `custom_module`: Optional module path for custom hash implementations
- `custom_function`: Optional function name for custom hash implementations
- `custom_hash_length`: Optional output length for custom hash functions

### Environment Variables

The following environment variables can be used to configure the system:

```bash
# Database Configuration
MCARD_STORE_DB_PATH=path/to/db.db
MCARD_STORE_MAX_CONNECTIONS=10
MCARD_STORE_TIMEOUT=60.0

# Hash Configuration
MCARD_HASH_ALGORITHM=sha256
MCARD_HASH_CUSTOM_MODULE=my_hash_module
MCARD_HASH_CUSTOM_FUNCTION=my_hash_func
MCARD_HASH_CUSTOM_LENGTH=32
```

### Test Configuration

The test suite uses a dedicated configuration setup that ensures:
- Isolated test environments with separate database paths
- Clean environment variables between tests
- Reproducible test conditions
- Prevention of test cross-contamination

Test-specific settings can be defined in `tests/.env.test` for consistent test environments.

### Design Patterns

The configuration system implements several design patterns:
- **Singleton Pattern**: Ensures a single, consistent configuration instance
- **Strategy Pattern**: Supports different configuration sources
- **Builder Pattern**: Validates and constructs configuration objects
- **Immutable Configuration**: Prevents runtime configuration changes

### Usage Example

```python
from mcard.infrastructure.config import load_config

# Load configuration (automatically detects environment)
config = load_config()

# Access configuration values
db_path = config.repository.db_path
max_conn = config.repository.max_connections
hash_algo = config.hashing.algorithm

# Configuration is immutable after loading
# Attempting to modify will raise RuntimeError
```

## Project Structure

- `mcard/`: Contains the core library code.
- `tests/`: Includes all test cases.
- `examples/`: Provides example scripts demonstrating library usage.

## Recent Changes

- Updated the handling of the `g_time` field in the `CardResponse` model.
- Modified the `create_card`, `get_card`, and `list_cards` functions to ensure the correct handling of `g_time` as a string.

## Usage

### Basic Usage

```python
from mcard import MCard, get_now_with_located_zone
from mcard import HashingSettings, CollisionAwareHashingService

# Create a card with default SHA-256 hashing
card = MCard(content="Hello, World!")
print(f"Hash (SHA-256): {card.hash}")
print(f"Global Time: {card.g_time}")  # e.g., 2024-01-24 15:30:45.123456+00:00

# Use collision-aware hashing with automatic algorithm strengthening
settings = HashingSettings(algorithm="md5")  # Starts with MD5
service = CollisionAwareHashingService(settings)
card = MCard(content="Hello, World!", hashing_service=service)
print(f"Initial Hash (MD5): {card.hash}")

# If a collision is detected, it automatically upgrades to stronger algorithms
collision_content = "Different content with same MD5"
card2 = MCard(content=collision_content, hashing_service=service)
print(f"New Hash (Stronger Algorithm): {card2.hash}")

# Create a card with explicit global time
now = get_now_with_located_zone()  # Microsecond precision timestamp
card = MCard(content="Hello, World!", g_time=now)
```

### Storage and Collections

```python
from mcard import SQLiteCardRepository, MCardCollection

# Initialize storage with SQLite backend
storage = SQLiteCardRepository("cards.db")

# Create a collection
collection = MCardCollection(storage)

# Add cards to collection
card1 = MCard(content="First card")
card2 = MCard(content="Second card")

collection.add_card(card1)
collection.add_card(card2)

# Retrieve cards (always sorted by g_time)
all_cards = collection.get_all_cards()
card = collection.get_card_by_hash(card1.hash)
```

### Time Management

```python
from mcard import TimeService, TimeSettings
from datetime import datetime, timedelta

# Initialize time service with custom settings
settings = TimeSettings(
    timezone="America/New_York",
    time_format="%Y-%m-%d %H:%M:%S %Z",
    use_utc=False
)
time_service = TimeService(settings)

# Get current time in configured timezone
now = time_service.get_current_time()

# Create and validate time ranges
start = now - timedelta(days=1)
end = now
time_range = time_service.create_time_range(start=start, end=end)

# Format times according to settings
formatted = time_service.format_time(now)

# Convert between timezones
utc_time = time_service.convert_timezone(now, "UTC")
```

### Advanced Features

#### Transaction Management
```python
from mcard import SQLiteCardRepository

# Create repository with connection pooling
storage = SQLiteCardRepository("cards.db", pool_size=5)

# Basic transaction
async with storage.transaction():
    await storage.save(card1)
    await storage.save(card2)  # If this fails, card1 is also rolled back

# Nested transactions with independent rollback
async with storage.transaction():  # Outer transaction
    await storage.save(card1)
    
    try:
        async with storage.transaction():  # Inner transaction using savepoint
            await storage.save(card2)
            raise ValueError("Something went wrong")
    except ValueError:
        pass  # Inner transaction rolls back to savepoint, card2 not saved
    
    await storage.save(card3)  # Still works, card1 and card3 are saved

# Thread-safe parallel transactions
async def task1():
    async with storage.transaction():
        await storage.save(card1)

async def task2():
    async with storage.transaction():
        await storage.save(card2)

await asyncio.gather(task1(), task2())  # Safe parallel execution
```

#### Batch Operations
```python
# Create multiple cards
cards = [MCard(content=f"Card {i}") for i in range(100)]

# Efficient batch save with transaction
with storage.transaction():
    saved, skipped = storage.save_many(cards)
print(f"Saved: {saved}, Skipped: {skipped}")

# Batch retrieve
hashes = [card.hash for card in cards]
retrieved = storage.get_many(hashes)

# Batch delete
deleted = storage.delete_many(hashes)
```

#### Time Range Queries
```python
from datetime import datetime, timedelta

# Get cards within a time range
start_time = datetime.now() - timedelta(hours=1)
end_time = datetime.now()
recent_cards = collection.get_cards_in_timerange(start_time, end_time)

# Get cards with pagination
page_size = 10
page_number = 1
cards = collection.get_cards_in_timerange(
    start_time,
    end_time,
    limit=page_size,
    offset=(page_number - 1) * page_size
)
```

## Configuration Management and Environment Variables

MCard Core supports flexible configuration through environment variables, allowing dynamic runtime configuration of key system parameters.

### Supported Configuration Parameters

| Environment Variable         | Description                                | Default Value       | Example                |
|------------------------------|--------------------------------------------|--------------------|------------------------|
| `MCARD_API_KEY`              | API authentication key                     | `default_mcard_api_key` | `test_custom_api_key_12345` |
| `MCARD_MANAGER_DB_PATH`      | Path to the SQLite database file           | `MCardManagerStore.db` | `test_custom_database.db` |
| `MCARD_MANAGER_DATA_SOURCE`  | Database backend type                      | `sqlite`           | `sqlite`               |
| `MCARD_MANAGER_POOL_SIZE`    | Connection pool size                       | `5`                | `3`                   |
| `MCARD_MANAGER_TIMEOUT`      | Database connection timeout (seconds)      | `30.0`             | `15.0`                |
| `MCARD_MANAGER_HASH_ALGORITHM` | Cryptographic hash algorithm             | `sha256`           | `sha512`              |

### Dynamic Configuration Loading

MCard Core implements a dynamic configuration loading mechanism that allows runtime configuration updates through environment variables. Key features include:

- Real-time environment variable parsing
- Flexible configuration reloading
- Secure default values
- Comprehensive type conversion

#### Example Configuration

```python
# Load configuration dynamically
app_settings = AppSettings(
    database=DatabaseSettings(
        db_path=os.getenv('MCARD_MANAGER_DB_PATH', 'default_database.db'),
        data_source=os.getenv('MCARD_MANAGER_DATA_SOURCE'),
        pool_size=int(os.getenv('MCARD_MANAGER_POOL_SIZE', 5)),
        timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', 30.0))
    ),
    mcard_api_key=os.getenv('MCARD_API_KEY', 'default_test_key')
)
```

### Configuration Testing

We provide comprehensive test scripts to validate configuration loading and environment variable handling:

- `test_mcard_config_env.py`: Verifies dynamic configuration loading
  - Tests API key configuration
  - Validates database path settings
  - Checks environment variable propagation
  - Ensures API functionality with custom configurations

### Best Practices

1. Use environment variables for sensitive configuration
2. Provide sensible default values
3. Validate and sanitize configuration inputs
4. Use secure methods for storing sensitive information

### Security Considerations

- Never hardcode sensitive credentials
- Use environment-specific configuration files
- Implement proper access controls
- Validate and sanitize all configuration inputs

## Debugging and Logging

Enable detailed logging to troubleshoot configuration issues:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Contribution

We welcome contributions to improve our configuration management system. Please submit issues or pull requests with suggestions for enhancement.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
