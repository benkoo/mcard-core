#!/usr/bin/env python3
"""
Script to safely clean up the MCard persistent database.
This script requires manual confirmation to proceed with deletion.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# Add the project root to the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

from mcard.storage import MCardStorage
from mcard import config

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
    parser = argparse.ArgumentParser(description="Clean up the MCard database with backup option.")
    parser.add_argument("--no-backup", action="store_true", help="Skip database backup")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    parser.add_argument("--test", action="store_true", help="Use test database")
    args = parser.parse_args()

    # Load environment variables
    config.load_config()

    # Initialize storage with appropriate database
    storage = MCardStorage(test=args.test)
    db_path = Path(storage.db_path)

    print(f"\nUsing database at: {db_path}")

    # Create backup unless --no-backup is specified
    if not args.no_backup:
        backup_path = backup_database(db_path)
    
    # Get current record information
    count, hashes = get_record_info(storage)
    
    # Get confirmation unless --force is specified
    if args.force or confirm_deletion(count, hashes):
        delete_all_records(storage)
        print("\nDatabase cleanup complete.")
    else:
        print("\nOperation cancelled.")
        sys.exit(1)

if __name__ == '__main__':
    main()
