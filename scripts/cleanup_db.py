#!/usr/bin/env python3
"""
Script to safely clean up the MCard persistent database.
This script requires manual confirmation to proceed with deletion.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil

try:
    import dotenv
    dotenv.load_dotenv(PROJECT_ROOT / ".env")
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("Warning: python-dotenv not found. Using default database path.")
    print("To install: pip install python-dotenv\n")

# Add the implementations/python directory to the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PYTHON_IMPL_DIR = PROJECT_ROOT / "implementations" / "python"
sys.path.append(str(PYTHON_IMPL_DIR))

from mcard.storage import MCardStorage

def backup_database(db_path: Path) -> Path:
    """Create a backup of the database before deletion."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
        print(f"Created backup at: {backup_path}")
    return backup_path

def get_record_info(storage: MCardStorage) -> tuple:
    """Get information about records in the database."""
    records = storage.get_all()
    return len(records), [record.content_hash[:8] for record in records]

def confirm_deletion(count: int, hashes: list) -> bool:
    """Ask for user confirmation before deletion."""
    print("\nDatabase Contents:")
    print(f"Total records: {count}")
    if count > 0:
        print("First few content hashes:")
        for i, hash_prefix in enumerate(hashes[:5]):
            print(f"  {i+1}. {hash_prefix}...")
        if len(hashes) > 5:
            print(f"  ... and {len(hashes) - 5} more")
    
    response = input("\nAre you sure you want to delete all records? (yes/no): ").lower()
    return response == 'yes'

def delete_all_records(storage: MCardStorage) -> int:
    """Delete all records from the database."""
    records = storage.get_all()
    deleted_count = 0
    total_count = len(records)
    
    print(f"\nDeleting {total_count} records...")
    for i, record in enumerate(records, 1):
        if storage.delete(record.content_hash):
            deleted_count += 1
        if i % 10 == 0:  # Progress update every 10 records
            print(f"Progress: {i}/{total_count} records processed")
    
    return deleted_count

def main():
    """Main function to handle database cleanup."""
    parser = argparse.ArgumentParser(description="Clean up MCard persistent database.")
    parser.add_argument('--no-backup', action='store_true', 
                      help="Skip creating a backup before deletion")
    parser.add_argument('--force', action='store_true',
                      help="Skip confirmation prompt")
    args = parser.parse_args()

    # Load environment variables
    if HAS_DOTENV and not dotenv.load_dotenv():
        print("Error: .env file not found")
        sys.exit(1)

    db_path = Path(os.getenv('MCARD_DB', 'data/db/MCardStore.db'))
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    print(f"Database path: {db_path}")
    
    # Create backup unless --no-backup is specified
    if not args.no_backup:
        backup_path = backup_database(db_path)
    
    # Initialize storage
    storage = MCardStorage(str(db_path))
    
    # Get current record count and sample hashes
    count, hashes = get_record_info(storage)
    
    # Get confirmation unless --force is specified
    if not args.force and not confirm_deletion(count, hashes):
        print("\nOperation cancelled")
        sys.exit(0)
    
    # Delete records
    deleted_count = delete_all_records(storage)
    
    print(f"\nOperation completed:")
    print(f"- Records deleted: {deleted_count}")
    if not args.no_backup:
        print(f"- Backup created: {backup_path}")

if __name__ == '__main__':
    main()
