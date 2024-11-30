# Sample Markdown Document

This is a sample markdown document to test MCard's text handling capabilities.

## Features
- Handles multiple file types
- Content-addressable storage
- Efficient retrieval

## Code Example
```python
async with MCardSetup() as setup:
    card = await setup.storage.create("Hello, World!")
    print(f"Hash: {card.hash}")
```
