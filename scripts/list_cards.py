#!/usr/bin/env python3

"""
Script to load and display all cards from the MCard database.
Attempts to decode binary content as UTF-8 text and shows original timezone information.
"""

import sys
import asyncio
from pathlib import Path
import argparse
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")

# Debug: Print environment variables
import os
print("Environment variables:")
print(f"MCARD_DB_PATH: {os.getenv('MCARD_DB_PATH')}")

from mcard import SQLiteCardRepository, AppSettings, DatabaseSettings
from mcard.domain.models.exceptions import StorageError

def format_content(content) -> str:
    """Format content for display, attempting to decode binary content as UTF-8."""
    if content is None:
        return "[Empty content]"
        
    if isinstance(content, str):
        content_str = content
    else:
        try:
            if isinstance(content, bytes):
                # Check if it looks like text
                if not any(b for b in content if b < 32 and b not in (9, 10, 13)):
                    content_str = content.decode('utf-8')
                else:
                    return f"[Binary content ({len(content)} bytes)]"
            else:
                content_str = str(content)
        except UnicodeDecodeError:
            return f"[Binary content ({len(content)} bytes)]"
    
    # Limit to 100 characters
    if len(content_str) > 100:
        return content_str[:100] + "..."
    return content_str

async def list_cards(db_path: Optional[str] = None, limit: Optional[int] = None) -> None:
    """List all cards in the database with optional limit."""
    try:
        # Load settings, override db_path if provided
        settings = AppSettings(
            database=DatabaseSettings(
                db_path=db_path or os.getenv('MCARD_DB_PATH'),
                pool_size=int(os.getenv('MCARD_DB_POOL_SIZE', '5')),
                timeout=float(os.getenv('MCARD_DB_TIMEOUT', '30.0'))
            )
        )
        
        print(f"Using database path: {settings.database.db_path}")
        
        # Create repository
        repo = SQLiteCardRepository(
            db_path=settings.database.db_path,
            pool_size=settings.database.pool_size
        )
        
        try:
            # Get all cards
            cards = await repo.get_all(limit=limit)
            
            if not cards:
                print("No cards found in the database.")
                return
            
            # Print header
            print(f"\nFound {len(cards)} cards in {settings.database.db_path}:")
            print("-" * 80)
            
            # Print each card
            for card in cards:
                content = format_content(card.content)
                print(f"Hash: {card.hash}")
                print(f"Time: {card.g_time.isoformat()}")
                print(f"Content: {content}")
                print("-" * 80)
                
        finally:
            # Always close the repository
            await repo.close()
            
    except StorageError as e:
        print(f"Error accessing database: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

def main():
    """Parse arguments and run the script."""
    parser = argparse.ArgumentParser(description="List all cards in the MCard database.")
    parser.add_argument("--db", help="Path to the database file (overrides MCARD_DB_PATH)")
    parser.add_argument("--limit", type=int, help="Maximum number of cards to display")
    args = parser.parse_args()
    
    asyncio.run(list_cards(db_path=args.db, limit=args.limit))

if __name__ == "__main__":
    main()
