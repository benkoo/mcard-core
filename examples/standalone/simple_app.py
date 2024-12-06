#!/usr/bin/env python3

import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from mcard.application.card_provisioning_app import CardProvisioningApp
from mcard.domain.services.hashing import get_hashing_service, HashingSettings
from mcard.infrastructure.setup import MCardSetup
from mcard.infrastructure.persistence.engine_config import EngineType

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """
    Main application entry point.
    """
    try:
        # Load environment variables from the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, '.env')

        if os.path.exists(env_path):
            logger.info(f"Loading environment from: {env_path}")
            load_dotenv(env_path, override=True)
        else:
            logger.warning("No .env file found")

        # Create MCardSetup instance using environment variables
        setup = MCardSetup(
            db_path=os.getenv('MCARD_STORE_PATH', 'data/db/simple_app.db'),
            engine_type=EngineType.SQLITE
        )
        await setup.initialize()

        # Load content from sample_data
        sample_data_dir = Path(script_dir) / 'sample_data'
        if not sample_data_dir.exists():
            logger.error(f"Sample data directory not found: {sample_data_dir}")
            return

        # Initialize CardProvisioningApp
        provisioning_app = CardProvisioningApp(setup.storage, get_hashing_service(HashingSettings()))

        # Load files into the MCard store
        for file_path in sample_data_dir.rglob('*'):
            if file_path.is_file():
                logger.info(f"Loading file: {file_path}")
                with open(file_path, 'rb') as f:
                    content = f.read()
                await provisioning_app.create_card(content)

        # Verify MCards are loaded
        all_cards = await provisioning_app.store.get_all()
        if all_cards is None:
            logger.error("Failed to retrieve MCards: all_cards is None")
            all_cards = []
        logger.info(f"Total MCards loaded: {len(all_cards)}")

        # Unload (delete) all MCards
        for card in all_cards:
            await provisioning_app.decommission_card(card.hash)

        # Verify MCards are unloaded
        all_cards_after = await provisioning_app.store.get_all()
        if all_cards_after is None:
            logger.error("Failed to retrieve MCards after unload: all_cards_after is None")
            all_cards_after = []
        logger.info(f"Total MCards remaining after unload: {len(all_cards_after)}")

        # Clean up
        await setup.cleanup()

    except Exception as e:
        logger.error("An error occurred:", exc_info=e)

if __name__ == "__main__":
    asyncio.run(main())
