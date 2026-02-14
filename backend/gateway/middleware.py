"""Middleware for logging and permissions."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log."""
        start_time = time.time()
        
        # Log request
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
        
        return response
