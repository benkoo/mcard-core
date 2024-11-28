from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from mcard.domain.models.exceptions import StorageError
import os
from pathlib import Path

# Importing configuration models
from mcard.domain.models.config import AppSettings, DatabaseSettings, HashingSettings
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardRepository
from mcard.infrastructure.persistence.schema_initializer import get_repository
from mcard.domain.services.hashing import get_hashing_service
from dotenv import load_dotenv

# Load environment variables from .env file
if os.getenv('TESTING') == 'true':
    test_env_path = Path(__file__).parent.parent.parent.parent / 'tests' / '.env.test'
    load_dotenv(test_env_path, override=True)
else:
    load_dotenv()

# Load application settings from environment
def load_app_settings():
    return AppSettings(
        database=DatabaseSettings(
            db_path=os.getenv('MCARD_MANAGER_DB_PATH', 'MCardManagerStore.db'),
            data_source=os.getenv('MCARD_MANAGER_DATA_SOURCE'),
            pool_size=int(os.getenv('MCARD_MANAGER_POOL_SIZE', 5)),
            timeout=float(os.getenv('MCARD_MANAGER_TIMEOUT', 30.0))
        ),
        hashing=HashingSettings(
            algorithm=os.getenv('MCARD_MANAGER_HASH_ALGORITHM', 'sha256'),
            custom_module=os.getenv('MCARD_MANAGER_CUSTOM_MODULE'),
            custom_function=os.getenv('MCARD_MANAGER_CUSTOM_FUNCTION'),
            custom_hash_length=int(os.getenv('MCARD_MANAGER_CUSTOM_HASH_LENGTH', 0))
        ),
        mcard_api_key=os.getenv('MCARD_API_KEY', 'default_mcard_api_key')
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

async def verify_api_key(x_api_key: str = Header(...), settings: AppSettings = Depends(load_app_settings)):
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
    g_time: str

@app.post("/cards/", response_model=CardResponse, status_code=201, dependencies=[Depends(verify_api_key)])
async def create_card(card: CardCreate, repo: CardRepository = Depends(get_repository)):
    print(f"Received request to create card with content: {card.content}")
    try:
        print(f"Repository instance ID during creation: {id(repo)}")
        print(f"Attempting to create card with content: {card.content}")
        content_bytes = card.content.encode('utf-8')
        hash_value = await get_hashing_service().hash_content(content_bytes)
        mcard = MCard(content=card.content, hash=hash_value)
        print(f"Repository instance ID during save: {id(repo)}")
        print(f"Attempting to save card with hash: {mcard.hash}")
        await repo.save(mcard)
        print(f"Card saved with hash: {mcard.hash}")
        print(f"Card created with hash: {mcard.hash}")
        g_time_str = mcard.g_time.isoformat() if isinstance(mcard.g_time, datetime) else mcard.g_time
        print(f"Created card: {mcard}")
        response_data = CardResponse(content=mcard.content, hash=mcard.hash, g_time=g_time_str)
        print(f"Returning response for created card: {response_data}")
        return response_data
    except Exception as e:
        print(f"Error creating card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cards/{hash_str}", response_model=CardResponse, dependencies=[Depends(verify_api_key)])
async def get_card(hash_str: str, repo: CardRepository = Depends(get_repository)):
    print(f"Received request to get card with hash: {hash_str}")
    print(f"Repository instance ID during retrieval: {id(repo)}")
    try:
        card = await repo.get(hash_str)
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")
        g_time_str = card.g_time.isoformat() if isinstance(card.g_time, datetime) else card.g_time
        return CardResponse(content=card.content, hash=card.hash, g_time=g_time_str)
    except StorageError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cards/", response_model=List[CardResponse], dependencies=[Depends(verify_api_key)])
async def list_cards(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    content: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    repo: CardRepository = Depends(get_repository)
):
    print("Received request to list cards")
    cards = await repo.get_all()
    
    # Apply filters
    if start_time:
        cards = [c for c in cards if c.g_time >= start_time]
    if end_time:
        cards = [c for c in cards if c.g_time <= end_time]
    if content:
        cards = [c for c in cards if content.lower() in c.content.lower()]
    
    # Sort by time
    cards.sort(key=lambda x: x.g_time, reverse=True)
    
    # Apply pagination
    if offset:
        cards = cards[offset:]
    if limit:
        cards = cards[:limit]
    
    return [CardResponse(content=card.content, hash=card.hash, g_time=card.g_time.isoformat() if isinstance(card.g_time, datetime) else card.g_time) for card in cards]

@app.delete("/cards/{hash_str}", status_code=204, dependencies=[Depends(verify_api_key)])
async def remove_card(hash_str: str, repo: CardRepository = Depends(get_repository)):
    print(f"Received request to remove card with hash: {hash_str}")
    
    try:
        # First check if the card exists
        card = await repo.get(hash_str)
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Then delete it
        await repo.delete(hash_str)
        print(f"Removed card with hash: {hash_str}")
        return None
    except Exception as e:
        print(f"Error removing card: {e}")
        raise HTTPException(status_code=500, detail=str(e))
