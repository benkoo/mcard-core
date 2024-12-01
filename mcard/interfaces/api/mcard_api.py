"""MCard API implementation."""
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from mcard.domain.models.exceptions import StorageError
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=os.getenv("MCARD_SERVICE_LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importing configuration models
from mcard.domain.models.config import AppSettings, HashingSettings, DatabaseSettings
from mcard.infrastructure.persistence.engine_config import SQLiteConfig
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardStore
from mcard.infrastructure.persistence.async_persistence_wrapper import AsyncPersistenceWrapper
from mcard.domain.services.hashing import get_hashing_service
from mcard.application.card_provisioning_app import CardProvisioningApp
from dotenv import load_dotenv

# Load environment variables from .env file
if os.getenv('TESTING') == 'true':
    test_env_path = Path(__file__).parent.parent.parent.parent / 'tests' / '.env.test'
    load_dotenv(test_env_path, override=True)
else:
    load_dotenv()

# Load application settings from environment
def load_config():
    """Load application settings from environment variables."""
    return AppSettings(
        database=DatabaseSettings(
            db_path=os.getenv('MCARD_MANAGER_DB_PATH', 'MCardManagerStore.db'),
            max_connections=int(os.getenv('MCARD_MANAGER_POOL_SIZE', '5')),
            timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', '30.0')),
            data_source='sqlite'
        ),
        hashing=HashingSettings(
            algorithm=os.getenv('MCARD_MANAGER_HASH_ALGORITHM', 'sha256'),
            custom_module=os.getenv('MCARD_MANAGER_CUSTOM_MODULE'),
            custom_function=os.getenv('MCARD_MANAGER_CUSTOM_FUNCTION'),
            custom_hash_length=int(os.getenv('MCARD_MANAGER_CUSTOM_HASH_LENGTH', '0'))
        ),
        mcard_api_key=os.getenv('MCARD_API_KEY', 'default_mcard_api_key'),
        mcard_api_port=int(os.getenv('MCARD_API_PORT', '3001'))
    )

# Debug logging for API key verification
def debug_api_key_verification(x_api_key: str, settings: AppSettings):
    print("DEBUGGING API KEY VERIFICATION")
    print(f"x_api_key type: {type(x_api_key)}")
    print(f"x_api_key value: {repr(x_api_key)}")
    print(f"MCARD_API_KEY type: {type(settings.mcard_api_key)}")
    print(f"MCARD_API_KEY value: {repr(settings.mcard_api_key)}")
    if x_api_key != settings.mcard_api_key:
        print(f"API Key Verification Failed - Received: {repr(x_api_key)}, Expected: {repr(settings.mcard_api_key)}")

async def verify_api_key(x_api_key: Optional[str] = Header(None), settings: AppSettings = Depends(load_config)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key required")
    debug_api_key_verification(x_api_key, settings)
    if x_api_key != settings.mcard_api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True

app = FastAPI(title="MCard API", description="API for managing MCard content")

class CardCreate(BaseModel):
    content: str

class CardResponse(BaseModel):
    content: str
    hash: str
    g_time: Optional[datetime]

async def get_store() -> CardStore:
    """Get store instance."""
    settings = load_config()
    config = SQLiteConfig(
        db_path=settings.database.db_path,
        max_connections=settings.database.max_connections,
        timeout=settings.database.timeout
    )
    return AsyncPersistenceWrapper(config)

class MCardAPI:
    """API wrapper for MCard operations."""
    
    def __init__(self, store: Optional[CardStore] = None, repository: Optional[CardStore] = None):
        """Initialize MCardAPI with a store or repository."""
        self.store = store or repository
        if self.store is None:
            raise ValueError("Either store or repository must be provided")
        self.app = CardProvisioningApp(self.store)

    async def create_card(self, content: str) -> MCard:
        """Create a new card with the given content."""
        try:
            return await self.app.create_card(content)
        except StorageError as e:
            logger.error(f"Failed to create card: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_card(self, hash_str: str) -> MCard:
        """Get a card by its hash."""
        try:
            card = await self.app.retrieve_card(hash_str)
            if not card:
                raise HTTPException(status_code=404, detail=f"Card with hash {hash_str} not found")
            return card
        except StorageError as e:
            logger.error(f"Failed to get card: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_cards(self, content: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[MCard]:
        """List cards with optional filtering and pagination."""
        try:
            return await self.app.list_cards_by_content(content=content, limit=limit, offset=offset)
        except StorageError as e:
            logger.error(f"Failed to list cards: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def remove_card(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        try:
            await self.app.decommission_card(hash_str)
        except StorageError as e:
            logger.error(f"Failed to remove card: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize the store on startup."""
    try:
        # Test store connection and initialize schema
        repo = await get_store()
        await repo.get_all(limit=1)
        logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"store initialization failed with error: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Get the current store instance and close it
        repo = await get_store()
        await repo.close()
        logger.info("store closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"status": "ok"}

@app.post("/cards/", response_model=CardResponse, dependencies=[Depends(verify_api_key)])
async def create_card(card: CardCreate, repo: CardStore = Depends(get_store)):
    api = MCardAPI(repo)
    result = await api.create_card(card.content)
    return CardResponse(
        content=result.content,
        hash=result.hash,
        g_time=result.g_time
    )

@app.get("/cards/{hash_str}", response_model=CardResponse, dependencies=[Depends(verify_api_key)])
async def get_card(hash_str: str, repo: CardStore = Depends(get_store)):
    api = MCardAPI(repo)
    result = await api.get_card(hash_str)
    return CardResponse(
        content=result.content,
        hash=result.hash,
        g_time=result.g_time
    )

@app.get("/cards/", response_model=List[CardResponse], dependencies=[Depends(verify_api_key)])
async def list_cards(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    content: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    repo: CardStore = Depends(get_store)
):
    api = MCardAPI(repo)
    results = await api.list_cards(content=content, limit=limit, offset=offset)
    if results is None:
        results = []
    return [
        CardResponse(
            content=card.content,
            hash=card.hash,
            g_time=card.g_time
        )
        for card in results
    ]

@app.delete("/cards/{hash_str}", status_code=204, dependencies=[Depends(verify_api_key)])
async def remove_card(hash_str: str, repo: CardStore = Depends(get_store)):
    api = MCardAPI(repo)
    await api.remove_card(hash_str)
    return {"message": "Card removed successfully"}
