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
- `time_claimed`: A timezone-aware timestamp with microsecond precision, used for ordering cards. This timestamp indicates when the content was claimed, preserving the exact order of card creation down to the microsecond.

These attributes ensure that:
1. Content can always be verified against its hash
2. Cards can always be totally ordered by their claim time
3. Content precedence can always be determined

## Installation

```bash
pip install mcard-core
```

## Usage

```python
from mcard import MCard

# Create an MCard - content_hash and time_claimed are automatically set
# maintaining algebraic closure
card = MCard(content="Hello World")

# Verify content integrity using the hash
print(card.content)  # "Hello World"
print(card.content_hash)  # "6861c3..." (SHA-256 hash guarantees content integrity)
print(card.time_claimed)  # Precise timestamp for ordering

# Different content types maintain the same properties
number_card = MCard(content=42)
dict_card = MCard(content={"key": "value"})
bytes_card = MCard(content=b"binary data")

# Store MCards in SQLite database while maintaining closure properties
from mcard import MCardStorage

# Initialize storage
storage = MCardStorage("mcards.db")

# Save MCard - database ensures uniqueness and maintains temporal order
storage.save(card)

# Retrieve by hash - content integrity is guaranteed
retrieved = storage.get(card.content_hash)

# Get all stored MCards (ordered by time_claimed)
# This ordering guarantees correct precedence relationships
all_cards = storage.get_all()
```

## Configuration

MCard uses environment variables for configuration. Create a `.env` file in your project root with the following parameters:

### Required Parameters

- `MCARD_DATA_SOURCE`: Path to the directory containing card data (e.g., `"data/cards"`)
- `MCARD_DB`: Path to the main database file (e.g., `"data/db/MCardStore.db"`)
- `MCARD_TEST_DB`: Path to the test database file (e.g., `"data/db/test/TESTONLY.db"`)

### Optional Parameters

- `MCARD_PERF_TEST_CARDS`: Number of cards to use in performance tests (default: 100)
  - Example: `MCARD_PERF_TEST_CARDS=500`
  - Set to a higher number for stress testing (e.g., 10000)
  - Set to a lower number for quick tests (e.g., 100)

Example `.env` file:
```ini
MCARD_DATA_SOURCE="data/cards"
MCARD_DB="data/db/MCardStore.db"
MCARD_TEST_DB="data/db/test/TESTONLY.db"

# Performance test configuration
MCARD_PERF_TEST_CARDS=500  # Number of cards to use in performance test
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcard-core.git
cd mcard-core
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment:
   - Copy `.env.example` to `.env` (if provided)
   - Modify the paths in `.env` to match your setup
   - Make sure the specified directories exist

5. Run tests:
```bash
pytest  # Run all tests
pytest tests/test_performance.py  # Run only performance tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
