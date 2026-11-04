"""Middleware for logging and permissions."""

import ipaddress
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Subnets considered "local" — localhost + RFC-1918 private ranges + WireGuard default
_LOCAL_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
]


def _is_local_ip(ip_str: str) -> bool:
    """Return True if the IP address is in a local/private range."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in _LOCAL_NETWORKS)
    except ValueError:
        return False


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging and remote-origin tagging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request, tag remote origin, and log."""
        start_time = time.time()

        # Determine client IP (respect X-Forwarded-For from trusted proxies)
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # Tag whether this is a remote (non-local) request so guardrails can restrict tools
        is_remote = not _is_local_ip(client_ip)
        request.state.is_remote = is_remote
        request.state.client_ip = client_ip

        # Log request
        origin_tag = "remote" if is_remote else "local"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path} [{origin_tag}]")

        # Process request
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)"
        )

        return response
