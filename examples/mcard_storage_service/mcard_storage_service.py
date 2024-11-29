import os
import logging
import signal
import sys
from typing import Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, APIRouter, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Import MCard Core components
from mcard.interfaces.api.mcard_api import (
    app as mcard_app,
    CardResponse,
    CardCreate,
    verify_api_key,
    get_repository
)
from mcard.domain.models.config import AppSettings
from mcard.domain.models.exceptions import StorageError

# Load environment variables
if os.getenv('TESTING') == 'true':
    test_env_path = os.path.join(os.path.dirname(__file__), '..', 'tests', '.env.test')
    if os.path.exists(test_env_path):
        load_dotenv(test_env_path, override=True)
        logger = logging.getLogger(__name__)
        logger.debug(f"Loaded test environment from {test_env_path}")
else:
    load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("MCARD_SERVICE_LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCard Storage Service",
    description="A standalone storage service using MCard Core",
    version="1.0.0"
)

# Create router from MCard Core app
mcard_router = APIRouter()
for route in mcard_app.routes:
    mcard_router.routes.append(route)

# Include MCard Core routes
app.include_router(mcard_router, prefix="")

# Health check model
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    database_connected: bool

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of the service."""
    try:
        # Get repository to check database connection
        repo = await get_repository()
        # Try to access the database
        await repo.get_all(limit=1)
        database_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        database_connected = False
    
    return {
        "status": "healthy" if database_connected else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database_connected": database_connected
    }

# Service info model
class ServiceInfoResponse(BaseModel):
    name: str
    version: str
    uptime: float
    total_requests: int
    active_connections: int

# Track service metrics
start_time = datetime.utcnow()
request_count = 0

@app.get("/info", response_model=ServiceInfoResponse)
async def service_info(api_key: str = Depends(verify_api_key)):
    """Get service information and metrics."""
    global request_count
    request_count += 1
    
    current_time = datetime.utcnow()
    uptime = (current_time - start_time).total_seconds()
    
    return {
        "name": "MCard Storage Service",
        "version": "1.0.0",
        "uptime": uptime,
        "total_requests": request_count,
        "active_connections": 1  # Placeholder for now
    }

# Middleware to track requests and handle authentication
@app.middleware("http")
async def track_requests(request, call_next):
    """Track total requests and handle authentication."""
    # Skip authentication for health check endpoint
    if request.url.path == "/health":
        return await call_next(request)
    
    # Check for API key in header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return Response(
            content="API Key is required",
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return await call_next(request)

# Graceful shutdown handler
def handle_shutdown(signum, frame):
    """Handle graceful shutdown of the service."""
    logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)

# Register shutdown handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# Startup event handler
@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup."""
    try:
        # Test database connection
        repo = await get_repository()
        await repo.get_all(limit=1)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down service...")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("MCARD_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("MCARD_SERVICE_PORT", 8000))
    workers = int(os.getenv("MCARD_SERVICE_WORKERS", 1))
    
    uvicorn.run(
        "mcard_storage_service:app",
        host=host,
        port=port,
        workers=workers,
        reload=True
    )
