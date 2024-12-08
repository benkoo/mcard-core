#!/usr/bin/env python3
"""
Simple MCard file loading application.

This script recursively loads files from the sample_data directory 
into the MCard persistence service.
"""

import os
import asyncio
import logging
import traceback
from pathlib import Path
from dotenv import load_dotenv

from mcard.application.card_provisioning_app import CardProvisioningApp
from mcard.domain.services.hashing import get_hashing_service, HashingSettings
from mcard.infrastructure.setup import MCardSetup
from mcard.infrastructure.persistence.engine_config import EngineType
from mcard.domain.models.exceptions import StorageError, HashingError

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def load_file(provisioning_app, file_path):
    """
    Load a single file into the MCard persistence service.
    
    Args:
        provisioning_app (CardProvisioningApp): The card provisioning application
        file_path (Path): Path to the file to be loaded
    """
    try:
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
        
        logger.info(f"Processing file: {file_path} (size: {len(content)} bytes)")
        
        # Get hash before checking for duplicates
        content_hash = await provisioning_app.hashing_service.hash_content(content)
        logger.info(f"Generated hash for {file_path}: {content_hash}")
        
        # Check if content already exists
        if await provisioning_app.has_hash_for_content(content):
            # Get the existing card to check if it's a collision
            existing_card = await provisioning_app.store.get(content_hash)
            if existing_card:
                existing_content = existing_card.content
                if existing_content != content:
                    logger.warning(f"Hash collision detected!")
                    logger.warning(f"File: {file_path}")
                    logger.warning(f"Hash: {content_hash}")
                    logger.warning(f"Original content size: {len(existing_content)} bytes")
                    logger.warning(f"New content size: {len(content)} bytes")
                    
                    # Try to create card with stronger hash
                    try:
                        card = await provisioning_app.create_card(content)
                        logger.info(f"Successfully created card with stronger hash: {card.hash}")
                        return card
                    except Exception as e:
                        logger.error(f"Failed to create card with stronger hash: {e}")
                        return None
            
            logger.info(f"Skipping file with existing hash: {file_path}")
            return None
            
        # Create card
        card = await provisioning_app.create_card(content)
        logger.info(f"Successfully loaded file: {file_path} with hash: {card.hash}")
        return card
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        logger.error(traceback.format_exc())
        return None

async def load_files_recursively(provisioning_app, directory):
    """
    Recursively load files from a directory into the MCard persistence service.
    
    Args:
        provisioning_app (CardProvisioningApp): The card provisioning application
        directory (str or Path): Directory to recursively load files from
    """
    loaded_cards = []
    
    # Walk through directory
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip hidden files and directories
            if filename.startswith('.'):
                continue
            
            # Load file
            card = await load_file(provisioning_app, file_path)
            if card:
                loaded_cards.append(card)
    
    return loaded_cards

async def main():
    """
    Main application entry point.
    """
    try:
        # Load environment variables from the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, '.env')
        example_env_path = os.path.join(script_dir, '.env.example')
        
        # Try .env first, then .env.example
        if os.path.exists(env_path):
            logger.info(f"Loading environment from: {env_path}")
            load_dotenv(env_path, override=True)
        elif os.path.exists(example_env_path):
            logger.info(f"Loading environment from: {example_env_path}")
            load_dotenv(example_env_path, override=True)
        else:
            logger.warning("No .env or .env.example file found")

        # Get configuration from environment
        db_path = os.getenv('MCARD_DB_PATH')
        logger.info(f"Environment MCARD_DB_PATH: {db_path}")
        
        if not db_path:
            db_path = 'data/db/mcard_demo_md5.db'  # Use MD5-specific database
            logger.warning(f"MCARD_DB_PATH not set, using default: {db_path}")
            
        # Make db_path relative to script directory if it's not absolute
        if not os.path.isabs(db_path):
            db_path = os.path.join(script_dir, db_path)
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        logger.info(f"Using database path: {db_path}")
        
        # Create MCardSetup instance
        setup = MCardSetup(
            db_path=db_path,
            max_content_size=int(os.getenv('MCARD_MAX_CONTENT_SIZE', 10485760)),  # 10MB default
            max_connections=int(os.getenv('MCARD_MAX_CONNECTIONS', 5)),
            engine_type=EngineType.SQLITE,
            timeout=float(os.getenv('MCARD_TIMEOUT', 5.0))
        )
        
        # Log the absolute path of the database file
        logger.info(f"SQLite Database Path: {os.path.abspath(db_path)}")
        
        # Initialize storage
        await setup.initialize()
        
        # Initialize hashing service
        hash_settings = HashingSettings(
            algorithm=os.getenv('MCARD_HASH_ALGORITHM', 'sha1')
        )
        hashing_service = get_hashing_service(hash_settings)
        logger.info(f"Using hashing algorithm: {hash_settings.algorithm}")
        
        # Create provisioning app
        provisioning_app = CardProvisioningApp(setup.storage, hashing_service)
        
        # Debugging store information
        logger.info(f"Store type: {type(provisioning_app.store)}")
        logger.debug(f"Store attributes: {dir(provisioning_app.store)}")
        
        # Define sample data directory
        sample_data_dir = os.path.join(os.path.dirname(__file__), 'sample_data')
        
        # Load files recursively
        logger.info(f"Loading files from {sample_data_dir}")
        loaded_cards = await load_files_recursively(provisioning_app, sample_data_dir)
        
        # Print summary
        logger.info(f"Total files loaded: {len(loaded_cards)}")
        
        # List provisioned cards
        logger.debug(f"Attempting to list provisioned cards")
        try:
            all_cards = await provisioning_app.store.list() or []
            logger.debug(f"Raw list() result: {all_cards}")
            logger.info(f"Total cards in database: {len(all_cards)}")
        except Exception as e:
            logger.error(f"Error listing provisioned cards: {e}")
            logger.error(traceback.format_exc())
            all_cards = []
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Clean up
        await setup.cleanup()
        print(f"\nDatabase file location: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    asyncio.run(main())
