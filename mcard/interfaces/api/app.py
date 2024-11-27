"""
FastAPI application for MCard.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from ...domain.models.card import MCard
from ...domain.models.protocols import CardRepository
from ...infrastructure.repository import get_repository
from ...domain.services.hashing import get_hashing_service

app = FastAPI(title="MCard API", description="API for managing MCard content")

class CardCreate(BaseModel):
    """Schema for creating a new card."""
    content: str

class CardResponse(BaseModel):
    """Schema for card response."""
    content: str
    hash: str
    g_time: str

    class Config:
        from_attributes = True

async def get_card_repo() -> CardRepository:
    """Dependency injection for card repository."""
    return await get_repository()

@app.post("/cards/", response_model=CardResponse)
async def create_card(card: CardCreate, repo: CardRepository = Depends(get_card_repo)):
    """Create a new card."""
    # Convert content to bytes for hashing
    content_bytes = card.content.encode('utf-8')
    
    # Get hash from hashing service
    hash_value = await get_hashing_service().hash_content(content_bytes)
    
    # Create MCard with content and computed hash
    mcard = MCard(content=card.content, hash=hash_value)
    await repo.save(mcard)
    # Ensure g_time is formatted as a string
    if isinstance(mcard.g_time, datetime):
        g_time_str = mcard.g_time.isoformat()
    else:
        g_time_str = mcard.g_time

    return CardResponse(
        content=mcard.content,
        hash=mcard.hash,
        g_time=g_time_str
    )

@app.get("/cards/{hash_str}", response_model=CardResponse)
async def get_card(hash_str: str, repo: CardRepository = Depends(get_card_repo)):
    """Get a card by its hash."""
    card = await repo.get(hash_str)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    # Ensure g_time is formatted as a string
    if isinstance(card.g_time, datetime):
        g_time_str = card.g_time.isoformat()
    else:
        g_time_str = card.g_time

    return CardResponse(
        content=card.content,
        hash=card.hash,
        g_time=g_time_str
    )

@app.get("/cards/", response_model=List[CardResponse])
async def list_cards(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    repo: CardRepository = Depends(get_card_repo)
):
    """List cards with optional time range and pagination."""
    if start_time or end_time:
        cards = await repo.get_by_time_range(start_time, end_time, limit, offset)
    else:
        cards = await repo.get_all(limit, offset)
    # Ensure g_time is formatted as a string for all cards
    card_responses = []
    for card in cards:
        if isinstance(card.g_time, datetime):
            g_time_str = card.g_time.isoformat()
        else:
            g_time_str = card.g_time
        card_responses.append(CardResponse(
            content=card.content,
            hash=card.hash,
            g_time=g_time_str
        ))
    return card_responses
