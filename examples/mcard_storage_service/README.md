# MCard Interactive Demo

A demonstration CLI tool for the MCard content-addressable storage system. This interactive demo showcases the core capabilities of MCard, allowing users to create, retrieve, list, and search content-addressable cards.

## Features

- Interactive CLI interface
- Content-addressable storage using MCard
- Automatic content type detection
- Basic search functionality
- SQLite-based storage (in-memory or file-based)

## Prerequisites

- Python 3.x
- MCard Core library

## Usage

Run the interactive demo:

```bash
python mcard_interactive_demo.py [--db DB_PATH]
```

Options:
- `--db`: Path to SQLite database (defaults to in-memory database if not provided)

## Available Commands

1. **Create a new card**
   - Enter content for the card
   - Optionally specify content type
   - Returns the content hash of the created card

2. **Retrieve a card by hash**
   - Look up a card using its content hash
   - Displays card metadata and analysis

3. **List recent cards**
   - Shows recently created cards
   - Displays hash and creation time

4. **Search cards**
   - Search through card contents
   - Shows matching cards with preview

## Implementation Details

The demo uses the following core MCard components:
- `MCardStore` for persistence
- `ContentTypeInterpreter` for content analysis
- `MCard` data structure for content storage

## Example Usage

```python
# Initialize the CLI
cli = MCardInteractiveCLI(db_path="cards.db")

# Create a card
card = await cli.create_card("Hello, World!", "text/plain")

# Retrieve a card
retrieved_card = await cli.get_card(card.hash)

# Search cards
results = await cli.search_cards("Hello")
```

## License

Same as MCard Core
