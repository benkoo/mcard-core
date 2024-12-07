"""FastAPI server for MCard JavaScript bridge."""
from fastapi import FastAPI, HTTPException, Depends, Security, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from mcard.infrastructure.setup import MCardSetup
from mcard.domain.models.config import AppSettings
from mcard.config_constants import (
    ENV_API_PORT, 
    DEFAULT_API_PORT,
    ENV_DB_PATH, 
    DEFAULT_DB_PATH,
    ENV_DB_MAX_CONNECTIONS, 
    DEFAULT_POOL_SIZE,
    ENV_DB_TIMEOUT, 
    DEFAULT_TIMEOUT
)
from mcard.domain.models.card import MCard
from mcard.domain.dependency.interpreter import ContentTypeInterpreter
from pydantic import BaseModel, ValidationError, field_validator, Field
import os
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional
import asyncio
from contextlib import asynccontextmanager
import time
import xml.etree.ElementTree as ET
import yaml
import json
import base64
import string
import copy

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class CardRequest(BaseModel):
    """Request model for card operations."""
    content: str
    metadata: Optional[dict] = Field(default_factory=dict)

    @field_validator('content')
    def validate_content(cls, v):
        """Validate content field."""
        if not v:
            raise ValueError("Content cannot be empty")
        return v

    @field_validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata field."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v

class CardResponse(BaseModel):
    """Response model for card operations."""
    content: str
    hash: str
    g_time: str
    metadata: Optional[dict] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Hello World",
                    "hash": "abc123",
                    "g_time": "2024-12-07T09:59:01+07:00",
                    "metadata": {
                        "contentType": "text/plain"
                    }
                }
            ]
        }
    }

    @classmethod
    def from_mcard(cls, card: MCard):
        """Create a CardResponse from an MCard object."""
        metadata = card.metadata.copy() if hasattr(card, 'metadata') and card.metadata else {}
        
        return cls(
            content=card.content,
            hash=card.hash,
            g_time=card.g_time,
            metadata=metadata
        )

class PaginatedCardsResponse(BaseModel):
    """Response model for paginated card list."""
    items: List[CardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI application."""
    try:
        # Create setup instance
        app.state.setup = MCardSetup(
            db_path=os.getenv(ENV_DB_PATH, DEFAULT_DB_PATH),
            max_connections=int(os.getenv(ENV_DB_MAX_CONNECTIONS, str(DEFAULT_POOL_SIZE))),
            timeout=float(os.getenv(ENV_DB_TIMEOUT, str(DEFAULT_TIMEOUT)))
        )
        await app.state.setup.initialize()
        yield
    finally:
        if hasattr(app.state, 'setup'):
            await app.state.setup.cleanup()

app = FastAPI(lifespan=lifespan)

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
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

# Ensure data directory exists
data_dir = Path('./data')
data_dir.mkdir(exist_ok=True)

@app.get("/health")
async def health_check(api_key: str = Depends(get_api_key)):
    """Health check endpoint."""
    return {"status": "healthy"}

async def store_card(content: str, metadata: Optional[dict] = None):
    """Store card content and return its hash."""
    try:
        # Ensure metadata is a dictionary
        metadata = metadata.copy() if metadata else {}
        
        # Create MCard instance
        card = MCard(
            content=content,
            metadata=metadata,
            g_time=time.strftime("%Y-%m-%dT%H:%M:%S%z")
        )
        
        # Store the card
        await app.state.setup.storage.save(card)
        return card
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store card: {str(e)}")

def detect_content_type(content: str) -> tuple[str, dict]:
    """Detect content type and additional metadata for the content."""
    try:
        # Try to parse as JSON
        json.loads(content)
        return 'application/json', {'encoding': 'utf-8'}
    except json.JSONDecodeError:
        pass

    # Check for XML
    if content.strip().startswith('<?xml') or (content.strip().startswith('<') and '>' in content):
        return 'application/xml', {}

    # Check for CSV (simple heuristic)
    if ',' in content and '\n' in content:
        lines = content.strip().split('\n')
        if len(lines) > 1 and all(line.count(',') == lines[0].count(',') for line in lines):
            return 'text/csv', {'delimiter': ','}

    # Check for YAML
    if content.strip().startswith(('---', '{', '[')) and ':' in content:
        try:
            yaml.safe_load(content)
            return 'application/yaml', {'version': '1.2'}
        except yaml.YAMLError:
            pass

    # Check for Markdown
    if content.startswith('# ') or '**' in content or '*' in content or '[' in content and '](' in content:
        return 'text/markdown', {}

    # Check for binary (base64)
    try:
        base64.b64decode(content)
        return 'application/octet-stream', {'encoding': 'base64'}
    except:
        pass

    # Default to text/plain
    return 'text/plain', {}

async def create_card(content: str, metadata: Optional[dict] = None):
    """Create a new card with the given content and metadata."""
    try:
        # Create a deep copy of metadata to avoid modifying the input
        metadata = copy.deepcopy(metadata) if metadata else {}
        
        # Only detect content type if not provided by client
        if 'contentType' not in metadata:
            content_type, extra_metadata = detect_content_type(content)
            metadata['contentType'] = content_type
            metadata.update(extra_metadata)
        
        # Create MCard instance
        card = MCard(
            content=content,
            metadata=metadata,
            g_time=time.strftime("%Y-%m-%dT%H:%M:%S%z")
        )
        
        # Store the card
        await app.state.setup.storage.save(card)
        return card
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")

@app.post("/cards", response_model=CardResponse)
async def create_card_endpoint(card: CardRequest, api_key: str = Depends(get_api_key)):
    """Create a new card."""
    try:
        # Create card
        card_instance = await create_card(card.content, card.metadata)
        return CardResponse.from_mcard(card_instance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cards", response_model=PaginatedCardsResponse)
async def list_cards(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: str = Query("", description="Search term"),
    api_key: str = Depends(get_api_key)
):
    """List cards with pagination."""
    try:
        if search:
            # If search is provided, use search method
            cards, pagination_info = await app.state.setup.storage.search(
                query=search,
                search_content=True,
                search_hash=False,
                search_time=False,
                page=page,
                page_size=page_size
            )
        else:
            # Otherwise use list method
            cards, pagination_info = await app.state.setup.storage.list(
                page=page,
                page_size=page_size
            )
        
        # Convert to response model
        items = [CardResponse.from_mcard(card) for card in cards]
        
        return PaginatedCardsResponse(
            items=items,
            total=pagination_info['total'],
            page=pagination_info['page'],
            page_size=pagination_info['page_size'],
            total_pages=pagination_info['total_pages'],
            has_next=pagination_info['has_next'],
            has_previous=pagination_info['has_previous']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cards/{hash}", response_model=CardResponse)
async def get_card(hash: str, api_key: str = Depends(get_api_key)):
    """Get a card by hash."""
    try:
        card = await app.state.setup.storage.get(hash)
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")
        return CardResponse.from_mcard(card)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cards/{hash}")
async def delete_card(hash: str, api_key: str = Depends(get_api_key)):
    """Delete a card by hash."""
    try:
        # First check if card exists
        card = await app.state.setup.storage.get(hash)
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")
            
        # Delete the card and ensure it's deleted
        await app.state.setup.storage.delete(hash)
        
        # Verify the card is actually deleted
        deleted_card = await app.state.setup.storage.get(hash)
        if deleted_card is not None:
            raise HTTPException(status_code=500, detail="Failed to delete card")
            
        return {"message": "Card deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cards")
async def delete_all_cards(api_key: str = Depends(get_api_key)):
    """Delete all cards from the database."""
    try:
        await app.state.setup.storage.delete_all()
        return {"message": "All cards deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shutdown")
async def shutdown(api_key: str = Depends(get_api_key)):
    """Shutdown the server. Only used in test environment."""
    try:
        if not hasattr(app.state, 'setup'):
            raise HTTPException(status_code=500, detail="Database not initialized")
            
        # Clean up resources
        await app.state.setup.cleanup()
        
        # Schedule server shutdown
        def shutdown_server():
            import sys
            sys.exit(0)
            
        from threading import Timer
        Timer(0.1, shutdown_server).start()
        
        return {"message": "Server shutting down"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize app state on startup."""
    await setup_app()

async def setup_app():
    """Setup app state."""
    if not hasattr(app.state, 'setup'):
        app.state.setup = MCardSetup(
            db_path=os.getenv(ENV_DB_PATH, DEFAULT_DB_PATH),
            max_connections=int(os.getenv(ENV_DB_MAX_CONNECTIONS, str(DEFAULT_POOL_SIZE))),
            timeout=float(os.getenv(ENV_DB_TIMEOUT, str(DEFAULT_TIMEOUT)))
        )
        await app.state.setup.initialize()

@app.on_event("shutdown")
async def shutdown_app():
    """Cleanup app state."""
    if hasattr(app.state, 'setup'):
        await app.state.setup.storage.close()

if __name__ == "__main__":
    port = int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT))
    uvicorn.run(app, host="0.0.0.0", port=port)
