# MCard Storage Setup Guide

## Overview
The MCard setup module provides a flexible and reusable way to configure and initialize a CardStore storage system. It supports various database engines and configuration options, making it suitable for different application needs.

## Basic Usage

### In-Memory Store
```python
from mcard.infrastructure.setup import MCardSetup

async def main():
    async with MCardSetup() as store_setup:
        # Store setup provides access to the configured CardStore
        store = store_setup.storage
        # Use the store to create a card
        card = await store.create("Hello, World!")
        print(f"Created card with hash: {card.hash}")
```

### File-Based Store
```python
from mcard.infrastructure.setup import MCardSetup

async def main():
    store_setup = MCardSetup(db_path="/path/to/database.db")
    await store_setup.initialize()
    try:
        # Access the configured CardStore
        store = store_setup.storage
        card = await store.create("Hello, World!")
    finally:
        await store_setup.cleanup()
```

## Store Configuration

### Database Settings
```python
store_setup = MCardSetup(
    db_path="/path/to/database.db",
    max_connections=10,
    timeout=5.0,
    max_content_size=20 * 1024 * 1024  # 20MB
)
```

### Custom Configuration
```python
config_overrides = {
    "max_connections": 15,
    "timeout": 10.0,
    "check_same_thread": True
}

store_setup = MCardSetup(
    db_path="/path/to/database.db",
    config_overrides=config_overrides
)
```

## Store Features

### Content Type Detection
```python
async with MCardSetup() as store_setup:
    # Access the store's content interpreter
    interpreter = store_setup.content_interpreter
    content = b"Binary data"
    is_binary = interpreter.is_binary_content(content)
```

### Large Content Storage
```python
# Configure store for large content
store_setup = MCardSetup(
    max_content_size=100 * 1024 * 1024  # 100MB
)
```

## Multiple Store Instances

### Shared Database
```python
# Both instances will access the same underlying store
setup1 = MCardSetup(db_path="/path/to/database.db")
setup2 = MCardSetup(db_path="/path/to/database.db")

await setup1.initialize()
await setup2.initialize()
```

## Error Handling

### Storage Errors
```python
from mcard.domain.models.exceptions import StorageError

try:
    setup = MCardSetup(db_path="/invalid/path/database.db")
    await setup.initialize()
except StorageError as e:
    print(f"Storage error: {e}")
```

### Validation Errors
```python
from mcard.domain.models.exceptions import ValidationError

async with MCardSetup() as store_setup:
    try:
        # Attempt to store invalid content
        await store_setup.storage.create(None)
    except ValidationError as e:
        print(f"Validation error: {e}")
```

## Best Practices

1. **Use Context Managers**
   - Ensures proper cleanup of store resources
   - Handles errors gracefully
   - Simplifies code structure

2. **Configure Store Appropriately**
   - Set reasonable connection limits
   - Configure appropriate timeouts
   - Set content size limits based on needs

3. **Handle Errors**
   - Catch specific exceptions
   - Implement proper cleanup
   - Log errors appropriately

4. **Resource Management**
   - Close store connections when done
   - Don't share store instances across threads
   - Use connection pooling for high concurrency

## Performance Tips

1. **Connection Pooling**
   ```python
   setup = MCardSetup(
       max_connections=20,  # Increase for high concurrency
       timeout=3.0         # Decrease for faster failure
   )
   ```

2. **Content Size Limits**
   ```python
   # Balance between functionality and memory usage
   setup = MCardSetup(
       max_content_size=5 * 1024 * 1024  # 5MB
   )
   ```

3. **Database Location**
   ```python
   # Use local SSD for better performance
   setup = MCardSetup(
       db_path="/fast/local/ssd/database.db"
   )
   ```

## Testing

### Unit Tests
```python
import pytest
from mcard.infrastructure.setup import MCardSetup

@pytest.mark.asyncio
async def test_store_setup():
    async with MCardSetup() as store_setup:
        store = store_setup.storage
        card = await store.create("Test")
        assert card.content == "Test"
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_store_operations():
    setup = MCardSetup()
    await setup.initialize()
    try:
        store = setup.storage
        
        # Create card in store
        card1 = await store.create("Content 1")
        
        # Retrieve from store
        card2 = await store.get(card1.hash)
        assert card2.content == "Content 1"
        
        # List store contents
        cards = await store.list()
        assert len(cards) > 0
    finally:
        await setup.cleanup()
