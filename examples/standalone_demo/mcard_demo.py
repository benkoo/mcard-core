#!/usr/bin/env python3
"""
Demo script for MCard functionality.
"""

import os
import asyncio
import logging
import traceback
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

from mcard.application.card_provisioning_app import CardProvisioningApp
from mcard.domain.models.exceptions import StorageError, HashingError, MCardError
from mcard.domain.services.hashing import get_hashing_service, HashingSettings
from mcard.infrastructure.setup import MCardSetup
from mcard.infrastructure.persistence.engine_config import EngineType

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def process_file(provisioning_app: CardProvisioningApp, file_path: str) -> List[str]:
    """Process a single file."""
    results = []
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            
            # Get current hash before creating card
            try:
                initial_hash = await provisioning_app.hashing_service.hash_content(content)
                existing_card = await provisioning_app.retrieve_card(initial_hash)
            except Exception as e:
                logger.error(f"Error in process_file (hash/retrieve): {e}")
                logger.error(traceback.format_exc())
                results.append(f"Error retrieving card: {str(e)}")
                return results
            
            # Create the card (this will handle collisions and duplicates)
            try:
                card = await provisioning_app.create_card(content)
                if existing_card is not None:
                    if existing_card.hash == card.hash:
                        results.append(f"Found duplicate content in file: {os.path.basename(file_path)}")
                        results.append(f"Reusing existing card with hash: {card.hash}")
                    else:
                        results.append(f"Hash collision detected in file: {os.path.basename(file_path)}")
                        results.append(f"Created new card with stronger hash: {card.hash}")
                else:
                    results.append(f"Successfully processed new file: {os.path.basename(file_path)}")
                    results.append(f"Created card with hash: {card.hash}")
                results.append(f"Content length: {len(content)}")
            except Exception as e:
                logger.error(f"Error in process_file (create_card): {e}")
                logger.error(traceback.format_exc())
                results.append(f"Error creating card: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        logger.error(traceback.format_exc())
        results.append(f"Error processing file {file_path}: {str(e)}")
    return results


async def process_collision_files(provisioning_app: CardProvisioningApp, directory: str) -> List[str]:
    """Process all files in a directory."""
    results = []
    
    # Check if directory exists
    full_directory_path = os.path.join(os.path.dirname(__file__), 'sample_data', 'collisions', directory)
    if not os.path.exists(full_directory_path):
        logger.warning(f"Directory not found: {full_directory_path}")
        return results

    # List all files in the directory
    files = [f for f in os.listdir(full_directory_path) if os.path.isfile(os.path.join(full_directory_path, f))]
    
    if not files:
        logger.warning(f"No files found in directory: {full_directory_path}")
        return results

    for filename in files:
        file_path = os.path.join(full_directory_path, filename)
        try:
            file_results = await process_file(provisioning_app, file_path)
            results.extend(file_results)
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            logger.error(traceback.format_exc())
            results.append(f"Error processing file {filename}: {str(e)}")

    return results


async def main():
    """Main demo function."""
    try:
        # Load environment variables
        load_dotenv()

        # Initialize database with absolute path
        db_path = os.getenv('MCARD_DB_PATH', 'data/db/mcard_demo.db')
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        logger.info(f"Using database at: {db_path}")
        
        # Create MCardSetup instance
        setup = MCardSetup(
            db_path=db_path,
            max_content_size=int(os.getenv('MCARD_MAX_CONTENT_SIZE', 10485760)),  # 10MB default
            max_connections=int(os.getenv('MCARD_MAX_CONNECTIONS', 5)),
            engine_type=EngineType.SQLITE,
            timeout=5.0
        )
        
        try:
            # Initialize setup
            logger.info("Initializing storage...")
            await setup.initialize()
            logger.info("Storage initialized successfully")
            
            # Initialize services
            hash_settings = HashingSettings(algorithm=os.getenv('MCARD_HASH_ALGORITHM', 'sha1'))
            hashing_service = get_hashing_service(hash_settings)
            provisioning_app = CardProvisioningApp(setup.storage, hashing_service)

            # Print database status
            print("\nDatabase Status:")
            try:
                cards = await provisioning_app.list_provisioned_cards()
                num_cards = len(cards) if cards is not None else 0
                print(f"Database found at {db_path} with {num_cards} cards")
            except Exception as e:
                logger.error(f"Error accessing database: {e}")
                logger.error(traceback.format_exc())
                print(f"Error accessing database: {str(e)}")

            print(f"\nUsing hash algorithm: {hash_settings.algorithm}\n")

            # Demonstrate hash collisions
            print("Demonstrating hash collisions:\n")

            # Process MD5 collision test files
            print("Processing md5 collision test files:")
            try:
                results = await process_collision_files(provisioning_app, "md5")
                for result in results:
                    print(result)
            except Exception as e:
                logger.error(f"Error processing md5 files: {e}")
                logger.error(traceback.format_exc())
                print(f"Error processing md5 files: {str(e)}")

            # Process SHA1 collision test files
            print("\nProcessing sha1 collision test files:")
            try:
                results = await process_collision_files(provisioning_app, "sha1")
                for result in results:
                    print(result)
            except Exception as e:
                logger.error(f"Error processing sha1 files: {e}")
                logger.error(traceback.format_exc())
                print(f"Error processing sha1 files: {str(e)}")

            # Process test collision files
            print("\nProcessing test collision test files:")
            try:
                results = await process_collision_files(provisioning_app, "test")
                for result in results:
                    print(result)
            except Exception as e:
                logger.error(f"Error processing test files: {e}")
                logger.error(traceback.format_exc())
                print(f"Error processing test files: {str(e)}")

            # Process probability collision test files
            print("\nProcessing probability collision test files:")
            try:
                results = await process_collision_files(provisioning_app, "probability")
                for result in results:
                    print(result)
            except Exception as e:
                logger.error(f"Error processing probability files: {e}")
                logger.error(traceback.format_exc())
                print(f"Error processing probability files: {str(e)}")

        except Exception as e:
            logger.error(f"Error during processing: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            # Clean up
            logger.info("Cleaning up...")
            await setup.cleanup()
            logger.info("Cleanup complete")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    asyncio.run(main())
