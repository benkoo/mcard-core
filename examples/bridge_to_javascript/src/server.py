"""FastAPI server for MCard JavaScript bridge."""
# Standard library imports
import sys
import os
import time
import json
import asyncio
from typing import Optional, List
from pathlib import Path
from contextlib import asynccontextmanager

# Third-party library imports
import uvicorn
from dotenv import load_dotenv
from fastapi import (
    FastAPI, 
    HTTPException, 
    Depends, 
    Security, 
    Query
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import (
    BaseModel, 
    field_validator, 
    Field
)

# MCard specific imports
from mcard.infrastructure.setup import MCardSetup
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
from mcard.infrastructure.persistence.engine_config import EngineType
from mcard.domain.services.hashing import get_hashing_service

# Constants for server configuration
SERVER_HOST = "0.0.0.0"
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# Constants for search parameters
SEARCH_CONTENT_DEFAULT = True
SEARCH_HASH_DEFAULT = True
SEARCH_TIME_DEFAULT = True

# Constants for API key and security
API_KEY_HEADER_NAME = "X-API-Key"
DEFAULT_API_KEY = "default_key"

# Constants for HTTP status codes
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

# Constants for logging and error messages
ERROR_INVALID_API_KEY = "Invalid API key"
ERROR_CARD_NOT_FOUND = "Card not found"
ERROR_CARD_CREATION_FAILED = "Failed to create card"
ERROR_CARD_DELETION_FAILED = "Failed to delete card"
ERROR_SERVER_SHUTDOWN = "Server shutdown failed"

# Constants for error messages
ERROR_INVALID_CONTENT = "Content cannot be empty"
ERROR_INVALID_METADATA = "Metadata must be a dictionary"
ERROR_LISTING_CARDS = "Error listing cards"

# Constants for delete operations
ERROR_DELETE_ALL_CARDS_FAILED = "Failed to delete all cards"
SUCCESS_DELETE_ALL_CARDS = "All cards deleted successfully"

# Constants for health check
HEALTH_CHECK_SUCCESS = "Server is healthy"
HEALTH_CHECK_FAILURE = "Server health check failed"

# Additional configuration constants
CORS_ORIGINS = [
    "http://localhost:3000",  # Default React dev server
    "http://localhost:8000",  # Default FastAPI dev server
    "https://localhost:3000",
    "https://localhost:8000"
]

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration for MCardSetup
MCARD_SETUP_CONFIG = {
    'db_path': os.getenv(ENV_DB_PATH, DEFAULT_DB_PATH),
    'max_connections': int(os.getenv(ENV_DB_MAX_CONNECTIONS, DEFAULT_POOL_SIZE)),
    'timeout': float(os.getenv(ENV_DB_TIMEOUT, DEFAULT_TIMEOUT)),
    'engine_type': EngineType.SQLITE
}

class CardRequest(BaseModel):
    """Request model for card operations."""
    content: str
    metadata: Optional[dict] = Field(default_factory=dict)

    @field_validator('content')
    def validate_content(cls, v):
        """Validate content field."""
        if v is None or (isinstance(v, str) and v.strip() == ''):
            raise ValueError(ERROR_INVALID_CONTENT)
        return v

    @field_validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata field."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(ERROR_INVALID_METADATA)
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
        metadata = dict(card.metadata) if hasattr(card, 'metadata') and card.metadata else {}
        
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
    """
    Manage application lifespan events using async context manager.
    
    Performs the following actions:
    - Sets up MCard storage system on startup
    - Closes storage system on shutdown
    """
    try:
        # Startup logic
        if not hasattr(app.state, 'setup'):
            app.state.setup = MCardSetup(**MCARD_SETUP_CONFIG)
            await app.state.setup.initialize()
        
        print(f"Server started with configuration: {MCARD_SETUP_CONFIG}")
        
        yield  # Control is returned to the application
    
    except Exception as e:
        print(f"Startup error: {e}")
        raise
    
    finally:
        # Shutdown logic
        if hasattr(app.state, 'setup'):
            try:
                await app.state.setup.storage.close()
                print("Storage system closed successfully")
            except Exception as e:
                print(f"Error closing storage system: {e}")

app = FastAPI(
    title="MCard JavaScript Bridge",
    description="API for interacting with MCard storage system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME)

async def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key with improved error handling."""
    current_api_key = os.getenv('MCARD_API_KEY', DEFAULT_API_KEY)
    if api_key != current_api_key:
        raise HTTPException(
            status_code=HTTP_STATUS_FORBIDDEN,
            detail=ERROR_INVALID_API_KEY
        )
    return api_key

# Ensure data directory exists
data_dir = Path('./data')
data_dir.mkdir(exist_ok=True)

@app.delete("/cards")
async def delete_all_cards(api_key: str = Depends(get_api_key)):
    """
    Delete all cards from the database.
    
    Requires valid API key authentication.
    
    Returns:
        dict: Confirmation message of successful deletion
    
    Raises:
        HTTPException: If deletion fails
    """
    try:
        # Attempt to delete all cards
        await app.state.setup.storage.delete_all()
        return {"message": SUCCESS_DELETE_ALL_CARDS}
    except Exception as e:
        # Log the error for debugging
        print(f"Delete all cards error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR, 
            detail=f"{ERROR_DELETE_ALL_CARDS_FAILED}: {str(e)}"
        )

@app.get("/health")
async def health_check(api_key: str = Depends(get_api_key)):
    """
    Perform a health check on the server and storage system.
    
    Requires valid API key authentication.
    
    Returns:
        dict: Health status of the server
    
    Raises:
        HTTPException: If health check fails
    """
    try:
        # Check storage system initialization
        if not hasattr(app.state, 'setup'):
            raise ValueError("Storage system not initialized")
        
        # Attempt a simple storage operation to verify functionality
        await app.state.setup.storage.list(page=1, page_size=1)
        
        return {
            "status": "healthy",
            "message": HEALTH_CHECK_SUCCESS,
            "storage": {
                "type": str(type(app.state.setup.storage)),
                "config": MCARD_SETUP_CONFIG
            }
        }
    except Exception as e:
        # Log health check failure
        print(f"Health check error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR, 
            detail=f"{HEALTH_CHECK_FAILURE}: {str(e)}"
        )

async def store_card(content: str, metadata: Optional[dict] = None):
    """Store card content and return its hash."""
    try:
        # Ensure metadata is a dictionary
        metadata = dict(metadata) if metadata else {}
        
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
        # Create MCard instance directly without any additional processing
        card = MCard(
            content=content,
            metadata=metadata or {}
        )
        
        # Store the card
        await app.state.setup.storage.save(card)
        return card
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")

@app.post("/cards", response_model=CardResponse, status_code=201)
async def create_card_endpoint(
    card: CardRequest, 
    api_key: str = Depends(get_api_key)
):
    """Create a new card with minimal processing."""
    try:
        # Create card using MCard facility
        created_card = await create_card(card.content, card.metadata)
        
        # Convert to response model
        return CardResponse.from_mcard(created_card)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Card creation failed: {str(e)}")

@app.get("/cards", response_model=PaginatedCardsResponse)
async def list_cards(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE, description="Number of items per page"),
    search: str = Query("", description="Search term for partial matching in content, hash, or g_time"),
    search_content: bool = Query(SEARCH_CONTENT_DEFAULT, description="Search within card content"),
    search_hash: bool = Query(SEARCH_HASH_DEFAULT, description="Search within card hash"),
    search_time: bool = Query(SEARCH_TIME_DEFAULT, description="Search within card generation time"),
    api_key: str = Depends(get_api_key)
):
    """
    Retrieve a list of cards with optional search and pagination.

    Args:
        page: Page number for pagination (1-indexed)
        page_size: Number of cards per page
        search: Optional search term
        search_content: Whether to search in card content
        search_hash: Whether to search in card hash
        search_time: Whether to search in card time

    Returns:
        List of card dictionaries
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be positive")
    
    if page_size < MIN_PAGE_SIZE or page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"Page size must be between {MIN_PAGE_SIZE} and {MAX_PAGE_SIZE}")

    # Get the configured hashing service
    hashing_service = get_hashing_service()
    hash_algorithm = hashing_service.settings.algorithm

    # Perform search using the store's search method
    cards, pagination_info = await app.state.setup.storage.search(
        query=search,
        search_content=search_content,
        search_hash=search_hash,
        search_time=search_time,
        page=page,
        page_size=page_size
    )

    # Convert cards to list of dictionaries
    card_list = []
    for card in cards:
        card_dict = {
            'hash': card.hash,
            'content': card.content.decode('utf-8') if isinstance(card.content, bytes) else card.content,
            'g_time': card.g_time if isinstance(card.g_time, str) else card.g_time.isoformat() if card.g_time else None,
            'metadata': card.metadata or {}
        }
        card_list.append(card_dict)

    return PaginatedCardsResponse(
        items=[CardResponse(**card) for card in card_list],
        total=pagination_info.get('total', len(card_list)),
        page=page,
        page_size=page_size,
        total_pages=pagination_info.get('total_pages', (len(card_list) + page_size - 1) // page_size),
        has_next=pagination_info.get('has_next', page < (len(card_list) + page_size - 1) // page_size),
        has_previous=pagination_info.get('has_previous', page > 1)
    )

@app.get("/cards/{hash}", response_model=CardResponse)
async def get_card(
    hash: str, 
    api_key: str = Depends(get_api_key)
):
    """Retrieve a card by its hash with improved error handling."""
    try:
        # Attempt to retrieve the card
        card = await app.state.setup.storage.get(hash)
        
        if card is None:
            raise HTTPException(
                status_code=HTTP_STATUS_NOT_FOUND, 
                detail=f"{ERROR_CARD_NOT_FOUND}: {hash}"
            )
        
        return CardResponse.from_mcard(card)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"Card retrieval error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR, 
            detail=f"Error retrieving card: {str(e)}"
        )

@app.delete("/cards/{hash}", status_code=204)
async def delete_card(
    hash: str, 
    api_key: str = Depends(get_api_key)
):
    """Delete a card by its hash with improved error handling."""
    try:
        # Attempt to delete the card
        result = await app.state.setup.storage.delete(hash)
        
        # Always return 204 No Content, even if the card was not found
        return None
    except Exception as e:
        # Log unexpected errors
        print(f"Card deletion error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR, 
            detail=f"{ERROR_CARD_DELETION_FAILED}: {str(e)}"
        )

@app.post("/shutdown")
async def shutdown(api_key: str = Depends(get_api_key)):
    """Shutdown the server with improved error handling."""
    try:
        # Perform cleanup
        await app.state.setup.cleanup()
        
        # Attempt graceful shutdown
        import sys
        sys.exit(0)
    except Exception as e:
        # Log shutdown errors
        print(f"Shutdown error: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR, 
            detail=f"{ERROR_SERVER_SHUTDOWN}: {str(e)}"
        )

SERVER_STARTUP_BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                   MCard Bridge Server                        ║
╠══════════════════════════════════════════════════════════════╣
║ Host:     {host}                                             ║
║ Port:     {port}                                             ║
║ Database: {db_path}                                          ║
╚══════════════════════════════════════════════════════════════╝
"""

def configure_logging():
    """
    Configure logging for the application.
    
    Sets up basic logging configuration to provide 
    more informative console output during development.
    """
    import logging
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create a logger for the application
    logger = logging.getLogger('mcard_bridge')
    logger.setLevel(logging.INFO)
    
    return logger

def validate_environment():
    """
    Validate critical environment configurations before server startup.
    
    Checks:
    - Database path exists or can be created
    - API key is set
    - Required dependencies are available
    
    Raises:
        RuntimeError: If critical configuration is missing
    """
    # Validate database path
    db_path = Path(MCARD_SETUP_CONFIG['db_path']).parent
    if not db_path.exists():
        try:
            db_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Cannot create database directory: {db_path}") from e
    
    # Validate API key
    api_key = os.getenv('MCARD_API_KEY', DEFAULT_API_KEY)
    if api_key == DEFAULT_API_KEY:
        print("⚠️  Warning: Using default API key. This is not secure for production!")
    
    # Check required dependencies
    try:
        import mcard
        import fastapi
        import uvicorn
    except ImportError as e:
        raise RuntimeError(f"Missing required dependency: {e}")

def main():
    """
    Main entry point for the MCard Bridge Server.
    
    Handles server configuration, logging, and startup.
    """
    # Configure logging
    logger = configure_logging()
    
    try:
        # Validate environment and configurations
        validate_environment()
        
        # Retrieve port from environment, with fallback to default
        port = int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT))
        
        # Print startup banner
        print(SERVER_STARTUP_BANNER.format(
            host=SERVER_HOST, 
            port=port, 
            db_path=MCARD_SETUP_CONFIG['db_path']
        ))
        
        # Log server configuration
        logger.info(f"Starting MCard Bridge Server on {SERVER_HOST}:{port}")
        logger.info(f"Database Configuration: {MCARD_SETUP_CONFIG}")
        
        # Run the server with comprehensive configuration
        uvicorn.run(
            "server:app", 
            host=SERVER_HOST, 
            port=port, 
            reload=True,  # Auto-reload for development
            log_level="info",  # Detailed logging
            workers=1,  # Single worker for development
            proxy_headers=True,  # Support for reverse proxy
            forwarded_allow_ips="*"  # Allow all IPs (configure carefully in production)
        )
    
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
