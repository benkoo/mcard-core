"""FastAPI server for MCard JavaScript bridge."""
import os
import socket
import logging
import signal
import sys
from pathlib import Path

import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from mcard.config_constants import (
    ENV_API_PORT,
    DEFAULT_API_PORT,
    CORS_ORIGINS,
    SERVER_HOST,
    ENV_DB_PATH,
    DEFAULT_DB_PATH
)

from .mcard_api import app
from mcard.interfaces.api.api_config_loader import load_config

logger = logging.getLogger(__name__)

def find_free_port(start_port=DEFAULT_API_PORT):
    """Find a free port starting from the given port number."""
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    current_port = start_port
    max_attempts = 100

    for _ in range(max_attempts):
        if not is_port_in_use(current_port):
            return current_port
        current_port += 1

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def configure_app():
    """Configure the FastAPI application."""
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def handle_shutdown(signum, frame):
    """Handle shutdown signal."""
    logger.info("Received shutdown signal")
    sys.exit(0)

def main():
    """Main entry point for the MCard Bridge Server."""
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

        # Ensure data directory exists
        data_dir = Path('./data')
        data_dir.mkdir(exist_ok=True)

        # Load configuration
        config = load_config()
        
        # Get port from environment or find a free one
        port = int(os.getenv(ENV_API_PORT, '0'))
        if port == 0:
            port = find_free_port(start_port=DEFAULT_API_PORT)

        # Configure the FastAPI app
        configure_app()

        # Log startup information
        db_path = os.getenv(ENV_DB_PATH, DEFAULT_DB_PATH)
        logger.info(f"Using database at: {db_path}")
        logger.info(f"Starting server on {SERVER_HOST}:{port}")

        # Start the server
        uvicorn.run(app, host=SERVER_HOST, port=port)

    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
