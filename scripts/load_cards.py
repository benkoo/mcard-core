#!/usr/bin/env python3

"""
Script to load content from data/content directory into the MCard database.
Recursively finds all files and stores their content as MCard entries.
"""

import sys
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv
import mimetypes

# Add the project root to the Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# Load environment variables from .env file
ENV_FILE = PROJECT_ROOT / ".env"
print(f"Loading environment from: {ENV_FILE} (exists: {ENV_FILE.exists()})")
load_dotenv(ENV_FILE, override=True)

from mcard import SQLiteCardRepo, AppSettings, DatabaseSettings, MCard
from mcard.domain.models.domain_config_models import HashingSettings, HashAlgorithm
from mcard.domain.services.hashing import DefaultHashingService, set_hashing_service

print(f"MCARD_HASH_ALGORITHM environment variable: {os.environ.get('MCARD_HASH_ALGORITHM')}")
hash_algo = os.environ.get('MCARD_HASH_ALGORITHM', 'sha256')
hashing_settings = HashingSettings(algorithm=hash_algo)
print(f"Using hash algorithm: {hashing_settings.algorithm}")

# Initialize the hashing service with our settings and repository
hashing_service = DefaultHashingService(settings=hashing_settings)
set_hashing_service(hashing_service)

def is_binary(file_path: Path) -> bool:
    """Check if a file is binary based on its mimetype."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        # If we can't determine the type, try reading the first few bytes
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return True
    return not mime_type.startswith(('text/', 'application/json', 'application/xml'))

async def load_content(content_dir: Path, db_path: str) -> None:
    """Load all files from content_dir into the database."""
    try:
        # Initialize settings and repository
        settings = AppSettings(
            database=DatabaseSettings(
                db_path=db_path,
                pool_size=int(os.getenv('MCARD_DB_POOL_SIZE', '5')),
                timeout=float(os.getenv('MCARD_DB_TIMEOUT', '30.0'))
            )
        )
        
        repo = SQLiteCardRepo(
            db_path=settings.database.db_path,
            pool_size=settings.database.pool_size
        )

        try:
            # Find all files recursively
            files = [f for f in content_dir.rglob('*') if f.is_file()]
            print(f"\nFound {len(files)} files to process")
            
            # Process each file
            for file_path in files:
                rel_path = file_path.relative_to(content_dir)
                print(f"\nProcessing: {rel_path}")
                
                try:
                    # Read file content
                    if is_binary(file_path):
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        print("  (binary content)")
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        print(f"  Content length: {len(content)} characters")
                    
                    # Prepare content for hashing
                    if isinstance(content, str):
                        content_bytes = content.encode('utf-8')
                    elif isinstance(content, bytes):
                        content_bytes = content
                    else:
                        content_bytes = str(content).encode('utf-8')

                    # Compute hash first
                    hash_value = await hashing_service.hash_content(content_bytes)
                    
                    # Create and store card with pre-computed hash
                    card = MCard(content=content, hash=hash_value)
                    await repo.save(card)
                    print(f"  Stored as card with hash: {card.hash}")
                    
                except Exception as e:
                    print(f"  Error processing file: {e}", file=sys.stderr)
                    continue
            
            print("\nFinished processing all files")
            
        finally:
            # Always close the repository
            await repo.close()
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main entry point."""
    content_dir = PROJECT_ROOT / 'data' / 'content'
    db_path = os.getenv('MCARD_DB_PATH')
    
    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not db_path:
        print("Error: MCARD_DB_PATH environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    asyncio.run(load_content(content_dir, db_path))

if __name__ == "__main__":
    main()
