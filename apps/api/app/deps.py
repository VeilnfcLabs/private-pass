"""FastAPI dependencies for VeilPass API.

Provides rate limiting, API key authentication, and request ID injection.
"""

import time
from collections import defaultdict
from typing import Optional

from fastapi import Depends, Header, Request
from structlog import get_logger

from app.config import settings
from app.errors import InvalidTokenError, RateLimitedError
from app.utils import generate_id

logger = get_logger(__name__)

# ── In-memory token bucket rate limiter ───────────────────────────────────────


class TokenBucket:
    """Simple in-memory token bucket for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets: dict[str, dict] = defaultdict(
            lambda: {"tokens": capacity, "last_refill": time.monotonic()}
        )

    def consume(self, key: str, tokens: int = 1) -> bool:
        now = time.monotonic()
        bucket = self.buckets[key]

        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(
            self.capacity,
            bucket["tokens"] + elapsed * self.refill_rate,
        )
        bucket["last_refill"] = now

        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True
        return False


_rate_limiter = TokenBucket(capacity=settings.rate_limit, refill_rate=settings.rate_limit / 60.0)


async def rate_limit_dependency(request: Request) -> None:
    """Rate limiting dependency — uses client IP as the key."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else "unknown"
    )
    if not _rate_limiter.consume(client_ip):
        logger.warning("rate_limit_exceeded", ip=client_ip, path=str(request.url))
        raise RateLimitedError()


# ── API Key authentication ────────────────────────────────────────────────────


def _verify_api_key(key: str) -> bool:
    """Verify an API key.

    In production this would check against a database of API keys.
    For now it performs basic structural validation.
    """
    if not key or len(key) < 16:
        return False
    # Prefix-based validation: valid keys start with "vp_"
    if not key.startswith("vp_"):
        return False
    return True


async def api_key_dependency(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> str:
    """API key authentication dependency.

    Expects header: Authorization: Bearer <api_key>
    """
    if not authorization:
        raise InvalidTokenError("Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenError("Invalid Authorization header format")

    api_key = parts[1]
    if not _verify_api_key(api_key):
        raise InvalidTokenError("Invalid API key")

    return api_key


# ── Request ID ─────────────────────────────────────────────────────────────────


async def request_id_dependency(request: Request) -> str:
    """Generate or propagate a request ID."""
    req_id = request.headers.get("X-Request-ID", generate_id())
    request.state.request_id = req_id
    return req_id
