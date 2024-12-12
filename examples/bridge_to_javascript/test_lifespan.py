import os
import asyncio
import shutil
from src.server import MCARD_SETUP_CONFIG, lifespan
from fastapi import FastAPI

async def test_lifespan_schema_initialization():
    """
    Test the lifespan function's schema initialization behavior.
    
    This test will:
    1. Remove existing database file if it exists
    2. Create a new FastAPI app
    3. Run the lifespan context manager
    4. Verify that the database file is created and has non-zero size
    """
    # Get the database path from configuration
    db_path = MCARD_SETUP_CONFIG['db_path']
    db_dir = os.path.dirname(db_path)
    
    # Ensure the directory exists
    os.makedirs(db_dir, exist_ok=True)
    
    # Remove existing database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create a test FastAPI app
    app = FastAPI()
    
    try:
        # Run the lifespan context manager
        async with lifespan(app):
            # Check if database file was created
            assert os.path.exists(db_path), f"Database file {db_path} was not created"
            
            # Check if database file has non-zero size
            assert os.path.getsize(db_path) > 0, f"Database file {db_path} is empty"
            
            print("✅ Lifespan schema initialization test passed successfully!")
    
    except Exception as e:
        print(f"❌ Lifespan schema initialization test failed: {e}")
        raise

# Run the test
if __name__ == "__main__":
    asyncio.run(test_lifespan_schema_initialization())
