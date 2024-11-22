# MCard Core

A Python library for content-addressable data storage.

## Features

MCard provides a standardized way to handle content-addressable data with the following key attributes:

- `content`: The actual content data (can be any type)
- `content_hash`: A SHA-256 hash of the content (64-character hexadecimal string)
- `time_claimed`: A timezone-aware timestamp indicating when the content was claimed

## Installation

```bash
pip install mcard-core
```

## Usage

```python
from mcard import MCard

# Create an MCard with content and its hash
card = MCard(
    content="Hello World",
    content_hash="6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba"
)

# Access attributes
print(card.content)  # "Hello World"
print(card.content_hash)  # "6861c3..."
print(card.time_claimed)  # Current time with timezone

# Store MCards in SQLite database
from mcard import MCardStorage

# Initialize storage
storage = MCardStorage("mcards.db")

# Save MCard
storage.save(card)

# Retrieve by hash
retrieved = storage.get(card.content_hash)

# Get all stored MCards
all_cards = storage.get_all()
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

4. Run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
