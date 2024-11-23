# MCard Core

A Python library implementing an algebraically closed data structure for content-addressable storage. MCard ensures that every piece of content in the system is uniquely identified by its hash and temporally ordered by its claim time, enabling robust content verification and precedence ordering.

## Core Concepts

MCard implements an algebraically closed system where:
1. Every MCard is uniquely identified by its content hash
2. Every MCard has an associated claim time
3. The database maintains these invariants automatically

This design provides several key guarantees:
- **Content Integrity**: The content hash serves as both identifier and verification mechanism
- **Temporal Ordering**: All cards have a precise temporal order based on `time_claimed`
- **Precedence Verification**: The claim time enables determination of content presentation order
- **Algebraic Closure**: Any operation on MCards produces results that maintain these properties

## Features

Each MCard has three fundamental attributes that maintain the algebraic closure:

- `content`: The actual content data (can be any type)
- `content_hash`: A SHA-256 hash of the content, automatically calculated (64-character hexadecimal string)
- `time_claimed`: A timezone-aware timestamp with microsecond precision, used for ordering cards

These attributes ensure that:
1. Content can always be verified against its hash
2. Cards can always be totally ordered by their claim time
3. Content precedence can always be determined

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
print(card.content_hash)    # SHA-256 hash
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

# Retrieve cards
all_cards = collection.get_all_cards()  # Returns cards in temporal order
card = collection.get_card_by_hash(card1.content_hash)
```

### Thread Safety

When using MCard in a web application or multi-threaded environment, ensure proper connection management:

```python
from flask import Flask, g
from mcard import MCardStorage, MCardCollection

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

@app.teardown_appcontext
def teardown_db(exception):
    storage = g.pop('storage', None)
    if storage is not None:
        storage.conn.close()
```

## Examples

### Todo Application
A complete example of using MCard in a web application can be found in the `examples/todo_app` directory. This example demonstrates:
- Thread-safe database operations
- Proper transaction management
- Content-addressable storage for todo items
- Integration with Flask's application context
- Best practices for error handling and logging

See the [Todo App README](examples/todo_app/README.md) for more details.

## Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcard-core.git
cd mcard-core
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
```

4. Run tests:
```bash
pytest
```

## Project Structure

```
mcard-core/
├── mcard/              # Core library implementation
│   ├── core.py        # MCard class definition
│   ├── storage.py     # Storage implementation
│   └── collection.py  # Collection management
├── examples/          # Example applications
│   └── todo_app/     # Complete Todo application example
├── tests/            # Test suite
└── scripts/          # Utility scripts
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Best Practices

1. **Thread Safety**
   - Use thread-local storage in multi-threaded environments
   - Properly manage database connections
   - Use appropriate transaction management

2. **Error Handling**
   - Always use try/except blocks for database operations
   - Implement proper transaction rollback on errors
   - Include comprehensive error logging

3. **Data Integrity**
   - Verify content hashes when retrieving cards
   - Maintain proper temporal ordering
   - Use transaction-based updates for consistency

4. **Performance**
   - Close database connections when done
   - Use appropriate indexing for large collections
   - Implement proper connection pooling in web applications
