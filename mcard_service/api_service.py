from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from mcard.infrastructure.persistence.store import MCardStore
from mcard.domain.models.card import MCard
import asyncio

# Initialize FastAPI app
app = FastAPI(title="MCard Service API", description="API for MCard operations")

# Pydantic models for request and response
class CardCreate(BaseModel):
    content: str

class CardResponse(BaseModel):
    hash: str
    content: str
    g_time: Optional[str]

# Initialize MCardStore
store = MCardStore()

@app.post("/cards/", response_model=CardResponse)
async def create_card(card: CardCreate):
    try:
        new_card = MCard(content=card.content)
        await store.add(new_card)
        return CardResponse(hash=new_card.hash, content=new_card.content, g_time=new_card.g_time)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")

@app.get("/cards/{hash_str}", response_model=CardResponse)
async def get_card(hash_str: str):
    try:
        card = await store.get(hash_str)
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")
        return CardResponse(hash=card.hash, content=card.content, g_time=card.g_time)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")

@app.get("/cards/", response_model=List[CardResponse])
async def list_cards(limit: int = 10, offset: int = 0):
    try:
        cards = await store.list()
        paginated_cards = cards[offset:offset + limit]
        return [CardResponse(hash=card.hash, content=card.content, g_time=card.g_time) for card in paginated_cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cards: {str(e)}")

@app.delete("/cards/{hash_str}")
async def delete_card(hash_str: str):
    try:
        await store.remove(hash_str)
        return {"detail": "Card deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete card: {str(e)}")

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
