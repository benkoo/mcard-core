#!/usr/bin/env python3

"""
Script to clear all cards from the MCard database.
"""

import sys
from pathlib import Path
import os
import asyncio
from dotenv import load_dotenv

# Add the project root to the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# Load environment variables from .env file
ENV_FILE = PROJECT_ROOT / ".env"
print(f"Loading environment from: {ENV_FILE} (exists: {ENV_FILE.exists()})")
load_dotenv(ENV_FILE, override=True)

from mcard import SQLiteCardRepository

async def main():
    """Clear all cards from the database."""
    db_path = os.environ.get("MCARD_DB_PATH", "data/db/MCardStore.db")
    print(f"Using database path: {db_path}")

    # Create repository
    repo = SQLiteCardRepository(db_path)
    
    try:
        # Get all cards
        cards = await repo.get_all()
        if not cards:
            print("No cards found in the database.")
            return
        
        print(f"Found {len(cards)} cards. Deleting...")
        
        # Delete all cards
        await repo.delete_many([card.hash for card in cards])
        print("Successfully cleared all cards from the database.")
    finally:
        # Close repository connections
        await repo.close()

if __name__ == "__main__":
    asyncio.run(main())
