"""Data loading utility for MCard."""
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List
from .storage import MCardStorage
from .core import MCard
from . import config

def load_files_from_directory(directory: str) -> List[MCard]:
    """Load all files from the specified directory and convert them to MCards."""
    mcards = []
    directory_path = Path(directory).resolve()
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            try:
                # Read file content
                with open(file_path, "rb") as f:
                    content = f.read()
                
                # Try to decode as text if possible
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    pass  # Keep as binary if it's not text
                
                # Create MCard instance with content
                mcard = MCard(content=content)
                mcards.append(mcard)
                print(f"Loaded: {file_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
    
    return mcards

def main(test: bool = False):
    """Main function to load data into storage."""
    # Load environment variables
    config.load_config()
    
    # Get data source directory
    data_source = config.get_data_source()
    
    # Load all files from data source
    mcards = load_files_from_directory(data_source)
    print(f"Loaded {len(mcards)} cards from {data_source}")
    
    # Store in database
    storage = MCardStorage(test=test)
    for mcard in mcards:
        storage.save(mcard)
    print("All cards stored in database")

if __name__ == "__main__":
    main()
