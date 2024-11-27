from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import os
import logging

# Importing configuration models
from mcard.domain.models.config import AppSettings, DatabaseSettings, HashingSettings
from mcard.domain.models.card import MCard
from mcard.domain.models.protocols import CardRepository
from mcard.infrastructure.persistence.schema_initializer import get_repository
from mcard.domain.services.hashing import get_hashing_service

# Load application settings from environment
app_settings = AppSettings(
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

MCARD_API_KEY = 'test_api_key'

# Log the API key for debugging purposes
logging.debug(f"MCARD_API_KEY: {MCARD_API_KEY}")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcard_api.log"),
        logging.StreamHandler()
    ]
)

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != MCARD_API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate API key")

app = FastAPI(title="MCard API", description="API for managing MCard content")

class CardCreate(BaseModel):
    content: str

class CardResponse(BaseModel):
    content: str
    hash: str
    g_time: str

@app.post("/cards/", response_model=CardResponse, dependencies=[Depends(verify_api_key)])
async def create_card(card: CardCreate, repo: CardRepository = Depends(get_repository)):
    logging.debug(f"Received request to create card with content: {card.content}")
    try:
        logging.debug(f"Repository instance ID during creation: {id(repo)}")
        logging.debug(f"Attempting to create card with content: {card.content}")
        content_bytes = card.content.encode('utf-8')
        hash_value = await get_hashing_service().hash_content(content_bytes)
        mcard = MCard(content=card.content, hash=hash_value)
        logging.debug(f"Repository instance ID during save: {id(repo)}")
        logging.debug(f"Attempting to save card with hash: {mcard.hash}")
        await repo.save(mcard)
        logging.debug(f"Card saved with hash: {mcard.hash}")
        logging.debug(f"Card created with hash: {mcard.hash}")
        g_time_str = mcard.g_time.isoformat() if isinstance(mcard.g_time, datetime) else mcard.g_time
        logging.debug(f"Created card: {mcard}")
        response_data = CardResponse(content=mcard.content, hash=mcard.hash, g_time=g_time_str)
        logging.debug(f"Returning response for created card: {response_data}")
        return response_data
    except Exception as e:
        logging.error(f"Error creating card: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/cards/{hash_str}", response_model=CardResponse, dependencies=[Depends(verify_api_key)])
async def get_card(hash_str: str, repo: CardRepository = Depends(get_repository)):
    logging.debug(f"Received request to get card with hash: {hash_str}")
    logging.debug(f"Repository instance ID during retrieval: {id(repo)}")
    card = await repo.get(hash_str)
    if card is None:
        logging.warning(f"Card with hash {hash_str} not found")
        raise HTTPException(status_code=404, detail="Card not found")
    g_time_str = card.g_time.isoformat() if isinstance(card.g_time, datetime) else card.g_time
    return CardResponse(content=card.content, hash=card.hash, g_time=g_time_str)

@app.get("/cards/", response_model=List[CardResponse], dependencies=[Depends(verify_api_key)])
async def list_cards(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    repo: CardRepository = Depends(get_repository)
):
    logging.debug("Received request to list cards")
    cards = await repo.list(start_time=start_time, end_time=end_time, limit=limit, offset=offset)
    return [CardResponse(content=card.content, hash=card.hash, g_time=card.g_time.isoformat() if isinstance(card.g_time, datetime) else card.g_time) for card in cards]

@app.delete("/cards/{hash_str}", dependencies=[Depends(verify_api_key)])
async def remove_card(hash_str: str, repo: CardRepository = Depends(get_repository)):
    logging.debug(f"Received request to remove card with hash: {hash_str}")
    card = await repo.get(hash_str)
    if card is None:
        logging.warning(f"Card with hash {hash_str} not found")
        raise HTTPException(status_code=404, detail="Card not found")
    await repo.delete(card)
    logging.info(f"Removed card with hash: {hash_str}")
    return {"detail": "Card removed successfully"}
