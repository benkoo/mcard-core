# MCard Core

A wrapper class for content-addressable data with implementations in Python and TypeScript.

## Features

MCard provides a standardized way to handle content-addressable data with the following key attributes:

- `content`: The actual content data (can be any type)
- `content_hash`: A SHA-256 hash of the content (64-character hexadecimal string)
- `time_claimed`: A timezone-aware timestamp indicating when the content was claimed

## Installation

### Python
```bash
pip install mcard-core
```

### TypeScript
```bash
npm install @mcard/core
```

## Usage

### Python

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
```

### TypeScript

```typescript
import { MCard } from '@mcard/core';

// Create an MCard with content and its hash
const card = new MCard(
    "Hello World",
    "6861c3fdb3c1866563d1d0fa31664c836d992e1dcbcf1a4d517bbfecd3e5f5ba"
);

// Access attributes
console.log(card.content);  // "Hello World"
console.log(card.contentHash);  // "6861c3..."
console.log(card.timeclaimed);  // Current time
```

## Development

### Testing

Python:
```bash
python -m pytest implementations/python/tests/test_mcard.py -v
```

TypeScript:
```bash
cd implementations/typescript
npm test
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
