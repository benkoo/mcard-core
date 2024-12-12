"""MCard API implementation."""
from typing import List, Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from mcard.domain.models.exceptions import StorageError
from mcard.domain.models.card import MCard, CardCreate, CardResponse, PaginatedCardsResponse
from mcard.domain.models.protocols import CardStore
from mcard.infrastructure.persistence.async_persistence_wrapper import AsyncPersistenceWrapper
from mcard.infrastructure.persistence.database_engine_config import SQLiteConfig
from mcard.application.card_provisioning_app import CardProvisioningApp
from mcard.config_constants import ENV_SERVICE_LOG_LEVEL, ENV_DB_PATH, ENV_API_PORT, DEFAULT_API_PORT, DEFAULT_DB_PATH

from mcard.interfaces.api.api_config_loader import load_config
from .auth import verify_api_key, get_api_key_header

# Configure logging
logging.basicConfig(
    level=os.getenv(ENV_SERVICE_LOG_LEVEL, "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize store as None - will be lazily loaded
_store = None

app = FastAPI(title="MCard API", description="API for managing MCard content")

class MCardAPI:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MCardAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            # Additional initialization logic

    async def get_store(self) -> CardStore:
        """Get store instance lazily."""
        global _store
        if _store is None:
            settings = load_config()
            config = SQLiteConfig(
                db_path=settings.database.db_path,
                max_connections=settings.database.max_connections,
                timeout=settings.database.timeout
            )
            _store = AsyncPersistenceWrapper(config)  # Use the config directly to initialize the store
        return _store

    async def _init_app(self):
        """Initialize CardProvisioningApp lazily."""
        if not hasattr(self, 'card_provisioning_app'):
            store = await self.get_store()
            self.card_provisioning_app = CardProvisioningApp(store)
        return self.card_provisioning_app

    async def create_card(self, content: str) -> MCard:
        """Create a new card."""
        try:
            app = await self._init_app()
            return await app.create_card(content)
        except StorageError as e:
            logger.error(f"Failed to create card: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_card(self, hash_str: str) -> MCard:
        """Get a card by its hash."""
        try:
            app = await self._init_app()
            card = await app.retrieve_card(hash_str)
            if not card:
                raise HTTPException(status_code=404, detail="Card not found")
            return card
        except StorageError as e:
            logger.error(f"Failed to get card: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_cards(self, page: int, page_size: int) -> List[MCard]:
        """List cards with pagination."""
        app = await self._init_app()
        # Convert page and page_size to limit and offset
        offset = (page - 1) * page_size
        limit = page_size
        return await app.list_cards(limit=limit, offset=offset)

    async def remove_card(self, hash_str: str) -> None:
        """Remove a card by its hash."""
        try:
            app = await self._init_app()
            await app.decommission_card(hash_str)
        except StorageError as e:
            logger.error(f"Failed to remove card: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_all_cards(self) -> None:
        """Delete all cards."""
        app = await self._init_app()
        await app.delete_all_cards()

    async def health_check(self) -> dict:
        """Check API health."""
        try:
            store = await self.get_store()
            await store.get_all(limit=1)
            return {"status": "healthy"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_status(self):
        """Get the status of the API."""
        db_path = os.getenv(ENV_DB_PATH, DEFAULT_DB_PATH)
        port = os.getenv(ENV_API_PORT, str(DEFAULT_API_PORT))

        # Check if the API is healthy (you can implement more detailed health checks)
        healthy = True

        return {
            'status': 'healthy' if healthy else 'unhealthy',
            'port': port,
            'database_path': db_path
        }

    async def shutdown(self):
        """Shutdown the API and cleanup resources."""
        global _store
        if _store is not None:
            await _store.close()
            _store = None
            logger.info("API store closed and cleaned up")

# Initialize API instance
api = MCardAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize the store on startup."""
    try:
        await api.get_store()
        logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"Store initialization failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await api.shutdown()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "MCard API"}

@app.post("/cards", response_model=CardResponse)
async def create_card(card: CardCreate, _=Depends(verify_api_key)):
    """Create a new card."""
    result = await api.create_card(card.content)
    return result.to_api_response()

@app.get("/cards/{hash_str}", response_model=CardResponse)
async def get_card(hash_str: str, _=Depends(verify_api_key)):
    """Get a card by hash."""
    result = await api.get_card(hash_str)
    return CardResponse.from_mcard(result)

@app.get("/cards", response_model=PaginatedCardsResponse)
async def list_cards(
    page: int = 1,
    page_size: int = 10,
    _=Depends(verify_api_key)
):
    """List cards with pagination."""
    cards = await api.list_cards(page, page_size)
    return PaginatedCardsResponse(
        items=[CardResponse.from_mcard(card) for card in cards],
        total=len(cards),
        page=page,
        page_size=page_size
    )

@app.delete("/cards/{hash_str}")
async def remove_card(hash_str: str, _=Depends(verify_api_key)):
    """Remove a card by hash."""
    await api.remove_card(hash_str)
    return {"message": "Card deleted"}

@app.delete("/cards")
async def delete_all_cards(_=Depends(verify_api_key)):
    """Delete all cards."""
    await api.delete_all_cards()
    return {"message": "All cards deleted"}

@app.get("/health")
async def health_check(_=Depends(verify_api_key)):
    """Check API health."""
    return await api.health_check()

@app.get("/status")
async def get_status(_=Depends(verify_api_key)):
    """Get the status of the API."""
    return await api.get_status()
