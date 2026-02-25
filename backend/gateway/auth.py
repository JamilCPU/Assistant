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

    Behavior:
        - If no key is configured server-side (dev / local mode) → allow all requests.
        - If a key IS configured → the request must supply a matching X-API-Key header.

    Returns:
        API key string (may be empty string in dev mode).

    Raises:
        HTTPException 401: If a key is configured and the request is missing or wrong.
    """
    # Resolve the expected key: config file takes precedence, then env var.
    config = get_config()
    expected_key = config.get("server.api_key") or os.getenv("API_KEY")

    if not expected_key:
        # Dev / local mode: no key is configured, allow every request.
        return api_key or ""

    # A key is configured — the client must supply it.
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return api_key
