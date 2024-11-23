#!/usr/bin/env python3

"""
Script to load and display all cards from the MCard database.
Attempts to decode binary content as UTF-8 text and shows original timezone information.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from mcard.storage import MCardStorage
from mcard.collection import MCardCollection

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
    # Load environment variables
    load_dotenv()
    
    # Get database path from environment
    db_path = os.getenv('MCARD_DB')
    if not db_path:
        print("Error: MCARD_DB environment variable not set")
        return
    
    # Initialize storage and collection
    storage = MCardStorage(db_path)
    collection = MCardCollection(storage)
    
    # Get all cards
    cards = collection.get_all_cards()
    
    if not cards:
        print("No cards found in the database.")
        return
        
    # Print card information
    print(f"\nFound {len(cards)} cards in the database:\n")
    print("-" * 80)
    
    for i, card in enumerate(cards, 1):
        print(f"Card {i}:")
        print(f"Content Hash: {card.content_hash}")
        print(f"Time Claimed: {format_datetime(card.time_claimed)}")
        print(f"Content: {format_content(card.content)}")
        print("-" * 80)

if __name__ == "__main__":
    main()
