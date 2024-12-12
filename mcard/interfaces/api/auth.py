"""Authentication module for MCard API."""
import os
from typing import Optional
from mcard.domain.models.domain_config_models import AppSettings
from fastapi import Header, HTTPException, Depends
import logging

logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Optional[str] = Header(None), settings: AppSettings = None):
    """Verify the API key from request headers.
    
    Args:
        x_api_key: API key from request header
        settings: Application settings containing the valid API key
        
    Returns:
        bool: True if API key is valid
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key required")
    
    if settings and x_api_key != settings.mcard_api_key:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    return True

def get_api_key_header():
    """Get API key from request header."""
    async def api_key_header(x_api_key: str = Header(...)):
        return x_api_key
    return api_key_header
