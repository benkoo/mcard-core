#!/usr/bin/env python3

"""
Script to load and display all cards from the MCard database.
Attempts to decode binary content as UTF-8 text and shows original timezone information.
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add the project root to the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

from mcard.storage import MCardStorage
from mcard import config

def format_content(content):
    """
    Format content for display, attempting to decode binary content as UTF-8.
    Limits display to 100 characters.
    """
    # If content is already a string, use it directly
    if isinstance(content, str):
        content_str = content
    else:
        # Try to decode as UTF-8 if it's bytes
        try:
            if isinstance(content, bytes):
                content_str = content.decode('utf-8')
            else:
                content_str = str(content)
        except UnicodeDecodeError:
            return "[Binary content]"
    
    # Limit to 100 characters
    if len(content_str) > 100:
        return content_str[:100] + "..."
    return content_str

def format_datetime(dt):
    """
    Format datetime with timezone information.
    Shows both the time and the timezone name/offset.
    """
    # Format the date and time
    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Get timezone information
    if dt.tzinfo:
        # Get timezone name if available, otherwise use offset
        try:
            tz_name = dt.tzinfo.tzname(dt)
            if tz_name:
                tz_str = tz_name
            else:
                tz_str = dt.strftime('%z')  # Format: +HHMM or -HHMM
        except:
            tz_str = dt.strftime('%z')
    else:
        tz_str = 'UTC'
    
    return f"{time_str} {tz_str}"

def main():
    """Main function to list all cards in the database."""
    parser = argparse.ArgumentParser(description="List all cards in the MCard database.")
    parser.add_argument("--test", action="store_true", help="Use test database")
    args = parser.parse_args()

    # Load environment variables
    config.load_config()

    # Initialize storage with appropriate database
    storage = MCardStorage(test=args.test)
    print(f"\nUsing database at: {storage.db_path}\n")

    # Get all records
    records = storage.get_all()
    
    if not records:
        print("No cards found in database.")
        return

    # Print records
    print(f"Found {len(records)} cards:\n")
    for record in records:
        content = format_content(record.content)
        time_str = format_datetime(record.time_claimed)
        print(f"Hash: {record.content_hash}")
        print(f"Time: {time_str}")
        print(f"Content: {content}")
        print("-" * 80)

if __name__ == "__main__":
    main()
