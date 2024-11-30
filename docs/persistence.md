# MCard Persistence Layer

## Overview
The MCard persistence layer provides a flexible and extensible way to store and retrieve cards using different database backends. The architecture is designed to be database-agnostic while maintaining consistent behavior across different storage engines.

## Core Components

### AsyncPersistenceWrapper
The main interface for all database operations. It implements the `CardStore` protocol and delegates operations to the underlying database engine.

```python
from mcard.infrastructure.persistence.async_persistence_wrapper import AsyncPersistenceWrapper
from mcard.infrastructure.persistence.engine_config import SQLiteConfig

# Create wrapper with SQLite config
config = SQLiteConfig(db_path="database.db")
wrapper = AsyncPersistenceWrapper(config)

# Initialize
await wrapper.initialize()

# Use wrapper
card = await wrapper.create("content")
```

### BaseStore
Abstract base class that defines the interface for all database engines.

```python
from mcard.infrastructure.persistence.engine.base_engine import BaseStore

class CustomStore(BaseStore):
    async def save(self, card: MCard) -> None:
        # Implementation
        pass
        
    async def get(self, hash_str: str) -> Optional[MCard]:
        # Implementation
        pass
        
    # Other required methods
```

### SQLite Implementation
Reference implementation using SQLite as the storage backend.

```python
from mcard.infrastructure.persistence.engine.sqlite_engine import SQLiteStore
from mcard.infrastructure.persistence.engine_config import SQLiteConfig

# Create store
config = SQLiteConfig(db_path="database.db")
store = SQLiteStore(config)

# Initialize
await store.initialize()

# Use store
await store.save(card)
```

## Database Operations

### Save Operation
```python
# Create and save a card
card = MCard(content="Hello, World!")
await wrapper.save(card)
```

### Retrieve Operation
```python
# Get card by hash
card = await wrapper.get(hash_str)
if card:
    print(f"Content: {card.content}")
```

### List Operation
```python
# List recent cards
cards = await wrapper.list(limit=10)
for card in cards:
    print(f"Hash: {card.hash}, Content: {card.content}")
```

### Delete Operation
```python
# Remove a card
await wrapper.remove(hash_str)
```

## Configuration

### SQLite Configuration
```python
config = SQLiteConfig(
    db_path="database.db",
    max_connections=5,
    timeout=5.0,
    check_same_thread=False,
    max_content_size=10 * 1024 * 1024  # 10MB
)
```

### Custom Engine Configuration
```python
from mcard.infrastructure.persistence.engine_config import EngineConfig

class CustomConfig(EngineConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Custom configuration
        
    def create_store(self) -> BaseStore:
        return CustomStore(self)
```

## Error Handling

### Storage Errors
```python
from mcard.domain.models.exceptions import StorageError

try:
    await wrapper.save(card)
except StorageError as e:
    print(f"Storage error: {e}")
```

### Validation Errors
```python
from mcard.domain.models.exceptions import ValidationError

try:
    await wrapper.create(None)
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Best Practices

1. **Resource Management**
   ```python
   async with AsyncPersistenceWrapper(config) as wrapper:
       # Operations here
       pass  # Resources automatically cleaned up
   ```

2. **Batch Operations**
   ```python
   # More efficient than individual saves
   cards = [MCard(content=f"Content {i}") for i in range(10)]
   await wrapper.save_many(cards)
   ```

3. **Error Recovery**
   ```python
   from mcard.infrastructure.persistence.store import retry_operation

   @retry_operation(max_retries=3)
   async def save_with_retry(wrapper, card):
       await wrapper.save(card)
   ```

## Performance Considerations

1. **Connection Pooling**
   ```python
   config = SQLiteConfig(
       max_connections=20,  # Adjust based on load
       timeout=3.0         # Lower timeout for faster failure
   )
   ```

2. **Batch Processing**
   ```python
   # Process in batches for better performance
   async def process_batch(wrapper, items, batch_size=100):
       for i in range(0, len(items), batch_size):
           batch = items[i:i + batch_size]
           await wrapper.save_many(batch)
   ```

3. **Query Optimization**
   ```python
   # Use specific queries instead of listing all
   cards = await wrapper.list(
       start_time=start,
       end_time=end,
       limit=10
   )
   ```

## Testing

### Unit Tests
```python
@pytest.mark.asyncio
async def test_wrapper():
    config = SQLiteConfig(db_path=":memory:")
    wrapper = AsyncPersistenceWrapper(config)
    await wrapper.initialize()
    
    try:
        # Test operations
        card = await wrapper.create("Test")
        assert card.content == "Test"
    finally:
        await wrapper.close()
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_persistence():
    async with AsyncPersistenceWrapper(config) as wrapper:
        # Create
        card = await wrapper.create("Test")
        
        # Retrieve
        same_card = await wrapper.get(card.hash)
        assert same_card.content == card.content
        
        # List
        cards = await wrapper.list()
        assert len(cards) > 0
```
