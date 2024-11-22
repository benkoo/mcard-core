"""Data loading utility for MCard."""
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List
import dotenv
from .storage import MCardStorage
from .core import MCard

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

def main():
    """Main function to load data into storage."""
    # Load environment variables from project root
    project_root = Path(__file__).resolve().parents[3]  # Go up 3 levels to reach project root
    dotenv.load_dotenv(project_root / ".env")
    
    # Get data source directory and database path
    data_source = os.getenv("MCARD_DATA_SOURCE")
    db_path = os.getenv("MCARD_DB")
    
    if not data_source:
        raise ValueError("MCARD_DATA_SOURCE not set in environment")
    if not db_path:
        raise ValueError("MCARD_DB not set in environment")
    
    # Convert relative paths to absolute paths from project root
    data_source = str(project_root / data_source)
    db_path = str(project_root / db_path)
    
    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    # Initialize storage
    storage = MCardStorage(db_path)
    
    # Load and store files
    print(f"Loading files from {data_source}")
    mcards = load_files_from_directory(data_source)
    
    # Save to storage
    for mcard in mcards:
        storage.save(mcard)
        print(f"Saved MCard with hash: {mcard.content_hash}")
    
    print(f"Successfully loaded {len(mcards)} files")

if __name__ == "__main__":
    main()
