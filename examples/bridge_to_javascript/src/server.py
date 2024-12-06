"""FastAPI server for MCard JavaScript bridge."""
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from mcard.infrastructure.setup import MCardSetup
from mcard.domain.models.config import AppSettings
from mcard.config_constants import ENV_API_PORT, DEFAULT_API_PORT
from mcard.domain.models.card import MCard
from pydantic import BaseModel, ValidationError
import os
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class CardCreate(BaseModel):
    """Request model for card creation."""
    content: str

class CardResponse(BaseModel):
    """Response model for card operations."""
    content: str
    hash: str
    g_time: str

    @classmethod
    def from_mcard(cls, card: MCard):
        """Create a CardResponse from an MCard object."""
        return cls(
            content=card.content.decode('utf-8') if isinstance(card.content, bytes) else card.content,
            hash=card.hash,
            g_time=card.g_time  # g_time is already in ISO format
        )

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key."""
    current_api_key = os.getenv('MCARD_API_KEY', 'some_secure_key')
    if api_key != current_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key

# Ensure data directory exists
data_dir = Path('./data')
data_dir.mkdir(exist_ok=True)

# Initialize setup
@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    try:
        # Create setup instance
        app.state.setup = MCardSetup(
            db_path=os.getenv('MCARD_STORE_PATH', './data/mcard.db'),
            max_connections=int(os.getenv('MCARD_STORE_MAX_CONNECTIONS', '5')),
            timeout=float(os.getenv('MCARD_STORE_TIMEOUT', '5.0'))
        )
        await app.state.setup.initialize()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    if hasattr(app.state, 'setup'):
        await app.state.setup.cleanup()

@app.get("/health")
async def health_check(api_key: str = Depends(get_api_key)):
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/cards", response_model=CardResponse)
async def create_card(card: CardCreate, api_key: str = Depends(get_api_key)):
    """Create a new card."""
    if not card.content:
        raise HTTPException(status_code=400, detail="Content cannot be empty")
        
    try:
        if not hasattr(app.state, 'setup'):
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        result = await app.state.setup.storage.create(card.content)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create card")
        return CardResponse.from_mcard(result)
    except ValidationError as e:
        print(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error creating card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cards/{hash}", response_model=CardResponse)
async def get_card(hash: str, api_key: str = Depends(get_api_key)):
    """Get a card by hash."""
    try:
        if not hasattr(app.state, 'setup'):
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        card = await app.state.setup.storage.get(hash)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        return CardResponse.from_mcard(card)
    except Exception as e:
        print(f"Error getting card: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Card not found")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cards", response_model=List[CardResponse])
async def list_cards(api_key: str = Depends(get_api_key)):
    """List all cards."""
    try:
        if not hasattr(app.state, 'setup'):
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        cards = await app.state.setup.storage.list()
        return [CardResponse.from_mcard(card) for card in (cards or [])]
    except Exception as e:
        print(f"Error listing cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cards/{hash}")
async def delete_card(hash: str, api_key: str = Depends(get_api_key)):
    """Delete a card by hash."""
    try:
        if not hasattr(app.state, 'setup'):
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        # First check if the card exists
        card = await app.state.setup.storage.get(hash)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
            
        await app.state.setup.storage.remove(hash)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT))
    uvicorn.run(app, host="0.0.0.0", port=port)
