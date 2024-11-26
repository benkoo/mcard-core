# MCard Core

A Python library implementing an algebraically closed data structure for content-addressable storage. MCard ensures that every piece of content in the system is uniquely identified by its hash and temporally ordered by its claim time, enabling robust content verification and precedence ordering.

## Core Concepts

MCard implements an algebraically closed system where:
1. Every MCard is uniquely identified by its content hash (SHA-256)
2. Every MCard has an associated claim time (timezone-aware timestamp)
3. The database maintains these invariants automatically
4. Content integrity is guaranteed through immutable hashes
5. Temporal ordering is preserved at microsecond precision

This design provides several key guarantees:
- **Content Integrity**: The content hash serves as both identifier and verification mechanism
- **Temporal Ordering**: All cards have a precise temporal order based on `time_claimed`
- **Precedence Verification**: The claim time enables determination of content presentation order
- **Algebraic Closure**: Any operation on MCards produces results that maintain these properties
- **Type Safety**: Built on Pydantic with strict validation and type checking

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
- `content_hash`: An immutable SHA-256 hash, automatically calculated (64-character hex string)
- `time_claimed`: A timezone-aware timestamp with microsecond precision

### Storage Features
- SQLite-based persistent storage with connection pooling
- Binary content support
- Efficient batch operations for saving, retrieving, and deleting
- Transaction management with automatic rollback
- Thread-safe connection management
- Time-based query support
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
from mcard import MCard

# Create an MCard - content_hash and time_claimed are automatically set
card = MCard(content="Hello World")

# Access card properties
print(card.content)         # "Hello World"
print(card.content_hash)    # SHA-256 hash (64-character hex string)
print(card.time_claimed)    # Timezone-aware timestamp

# Content verification is automatic
card.content = "New content"  # Hash is automatically updated
```

### Storage and Collections

```python
from mcard import MCardStorage, MCardCollection

# Initialize storage with SQLite backend
storage = MCardStorage("cards.db")

# Create a collection
collection = MCardCollection(storage)

# Add cards to collection
card1 = MCard(content="First card")
card2 = MCard(content="Second card")

collection.add_card(card1)
collection.add_card(card2)

# Retrieve cards (always sorted by time_claimed)
all_cards = collection.get_all_cards()
card = collection.get_card_by_hash(card1.content_hash)
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

#### Batch Operations
```python
# Create multiple cards
cards = [MCard(content=f"Card {i}") for i in range(100)]

# Efficient batch save with transaction
with storage.transaction():
    saved, skipped = storage.save_many(cards)
print(f"Saved: {saved}, Skipped: {skipped}")

# Batch retrieve
hashes = [card.content_hash for card in cards]
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
export MCARD_TIMEZONE="America/New_York"
export MCARD_TIME_FORMAT="%Y-%m-%d %H:%M:%S %Z"
export MCARD_DATE_FORMAT="%Y-%m-%d"
export MCARD_USE_UTC=false

# Database settings
export MCARD_DB_PATH="cards.db"
export MCARD_POOL_SIZE=5
```

### Thread Safety

When using MCard in a web application or multi-threaded environment:

```python
from flask import Flask, g
from mcard import MCardStorage, MCardCollection, TimeService

app = Flask(__name__)
DB_PATH = "cards.db"

def get_storage():
    if 'storage' not in g:
        g.storage = MCardStorage(DB_PATH)
    return g.storage

def get_collection():
    if 'collection' not in g:
        g.collection = MCardCollection(get_storage())
    return g.collection

def get_time_service():
    if 'time_service' not in g:
        g.time_service = TimeService()
    return g.time_service

@app.teardown_appcontext
def teardown_db(exception):
    storage = g.pop('storage', None)
    if storage is not None:
        storage.close()
```

## Examples

### Todo Application
A complete example of using MCard in a web application can be found in the `examples/todo_app` directory. This example demonstrates:
- Thread-safe database operations
- Proper transaction management
- Content-addressable storage for todo items
- Integration with Flask's application context
- Best practices for error handling and logging
- Time-aware operations and timezone handling

See the [Todo App README](examples/todo_app/README.md) for more details.

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
