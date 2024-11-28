# Migration Guide: MCard Core 0.2.0

This guide helps you migrate from MCard Core 0.1.0 to 0.2.0, which introduces a more modular and maintainable architecture.

## Key Changes

1. **Domain-Driven Design**
   - Introduced clear separation between domain, infrastructure, and application layers
   - Better organization of code with dedicated modules for each concern
   - Improved testability and maintainability

2. **Async Support**
   - Repository operations are now async by default
   - Better handling of database connections
   - Improved performance for I/O operations

3. **Configuration**
   - New `AppSettings`, `HashingSettings`, and `DatabaseSettings` classes
   - Environment-based configuration with Pydantic
   - Better type safety and validation

4. **Error Handling**
   - Dedicated exception classes for different error types
   - More consistent error messages
   - Better error context

## Migration Steps

### 1. Update Dependencies

Add the following to your `requirements.txt`:
```
aiosqlite>=0.19.0
python-magic>=0.4.27
```

### 2. Code Changes

#### Before (0.1.0):
```python
from mcard import MCard, MCardStorage

# Create storage
storage = MCardStorage("cards.db")

# Save card
card = MCard(content="Hello, World!")
storage.save(card)

# Get card
retrieved = storage.get(card.content_hash)
```

#### After (0.2.0):
```python
import asyncio
from mcard import MCard, SQLiteCardRepository, CardService, ContentTypeInterpreter

async def main():
    # Initialize components
    repository = SQLiteCardRepository("cards.db")
    content_service = ContentTypeInterpreter()
    card_service = CardService(repository, content_service)

    # Create card
    card = await card_service.create_card("Hello, World!")

    # Get card
    retrieved = await card_service.get_card(card.content_hash)

# Run async code
asyncio.run(main())
```

### 3. Configuration Changes

#### Before (0.1.0):
```python
import os
os.environ["MCARD_DB_PATH"] = "cards.db"
```

#### After (0.2.0):
```python
from mcard import AppSettings, DatabaseSettings

# Load settings from environment
settings = AppSettings(
    database=DatabaseSettings(
        db_path="cards.db",
        pool_size=5
    )
)
```

## New Features

### 1. Content Type Detection
```python
from mcard import ContentTypeInterpreter

interpreter = ContentTypeInterpreter()
mime_type, extension = interpreter.detect_content_type(content)
```

### 2. Async Repository Operations
```python
async def process_cards():
    repository = SQLiteCardRepository("cards.db")
    
    # Get all cards
    cards = await repository.get_all()
    
    # Batch operations
    for card in cards:
        # Process each card
        await repository.save(card)
```

### 3. Error Handling
```python
from mcard.domain.models.exceptions import (
    MCardError,
    ValidationError,
    StorageError,
    HashingError
)

try:
    # Your code here
except ValidationError as e:
    print(f"Validation failed: {e}")
except StorageError as e:
    print(f"Storage operation failed: {e}")
except HashingError as e:
    print(f"Hashing operation failed: {e}")
except MCardError as e:
    print(f"General MCard error: {e}")
```

## Best Practices

1. **Use the CardService**
   - Prefer using `CardService` over direct repository access
   - It provides higher-level operations and proper validation

2. **Async/Await**
   - All database operations are async
   - Use proper async context managers and error handling
   - Consider using asyncio.gather for parallel operations

3. **Configuration**
   - Use Pydantic settings classes for type-safe configuration
   - Keep sensitive settings in environment variables
   - Use .env files for development

4. **Error Handling**
   - Catch specific exceptions rather than generic ones
   - Provide meaningful error messages
   - Use proper error context

## Breaking Changes

1. `MCardStorage` is replaced by `SQLiteCardRepository`
2. All repository operations are now async
3. Configuration is now handled by Pydantic settings classes
4. Direct access to hash functions is now through the hashing service

## Need Help?

If you encounter any issues during migration, please:
1. Check the example applications in the `examples` directory
2. Refer to the updated documentation
3. Open an issue on GitHub with details about your problem
