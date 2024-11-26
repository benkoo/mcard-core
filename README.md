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

Like HyperCard and HyperTalk before it, MCard aims to be a general-purpose programming system. However, it does so with a stronger theoretical foundation that enables:
- Formal verification of transformations
- Guaranteed composition properties
- Traceable data lineage
- Pure functional transformations

## Features

### Core MCard Attributes
- `content`: The actual content data (supports strings, bytes, and arbitrary types)
- `hash`: A cryptographic hash of the content, using SHA-256 by default (configurable to other algorithms)
- `g_time`: A timezone-aware timestamp with microsecond precision

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

## Installation

```bash
pip install mcard-core
```

## Requirements

- Python 3.8+
- pydantic >= 2.0.0

## Usage

### Basic Usage

```python
from mcard import MCard, get_now_with_located_zone
from mcard import HashingSettings

# Create a card with default SHA-256 hashing
card = MCard(content="Hello, World!")
print(f"Hash (SHA-256): {card.hash}")
print(f"Global Time: {card.g_time}")  # e.g., 2024-01-24 15:30:45.123456+00:00

# Configure different hashing algorithm
settings = HashingSettings(algorithm="blake2b")
card = MCard(content="Hello, World!", hashing_settings=settings)
print(f"Hash (BLAKE2b): {card.hash}")

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

### Configuration

MCard can be configured through environment variables:

```bash
# Time settings
export MCARD_TIMEZONE="America/New_York"  # Default timezone for timestamps
export MCARD_TIME_FORMAT="%Y-%m-%d %H:%M:%S %Z"  # Time format for display
export MCARD_DATE_FORMAT="%Y-%m-%d"  # Date format for display
export MCARD_USE_UTC=false  # Whether to use UTC for internal storage

# Database settings
export MCARD_DB_PATH="cards.db"  # SQLite database path
export MCARD_POOL_SIZE=5  # Connection pool size
```

### Thread Safety

MCard is designed to be thread-safe and can be safely used in multi-threaded or async environments:

```python
from mcard import SQLiteCardRepository, MCard

# Thread-safe connection pooling
storage = SQLiteCardRepository("cards.db", pool_size=5)

# Connections are automatically managed
async def worker():
    async with storage.transaction():
        card = MCard(content="Thread-safe content")
        await storage.save(card)

# Clean up when done
await storage.close()
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/benkoo/mcard-core.git
cd mcard-core
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
