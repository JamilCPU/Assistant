"""API key authentication."""

import os
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from backend.storage.config import get_config

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from header
        
    Returns:
        API key string if valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Get expected API key from config or environment
    config = get_config()
    expected_key = config.get("server.api_key")
    
    # Also check environment variable
    if not expected_key:
        expected_key = os.getenv("API_KEY")
    
    if not expected_key:
        # If no key configured, allow any key (development mode)
        # In production, you should always require a key
        return api_key
    
    if api_key != expected_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key
