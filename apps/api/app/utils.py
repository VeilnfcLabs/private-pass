"""Utility functions for VeilPass API."""

import secrets
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse


def generate_nonce() -> str:
    """Generate a unique nonce using uuid4 and urandom entropy."""
    return f"{uuid.uuid4().hex}{secrets.token_hex(16)}"


def generate_id() -> str:
    """Generate a short unique identifier."""
    return secrets.token_urlsafe(12)


def truncate_content(content: str, max_length: int = 4096) -> str:
    """Truncate content for QR inputs that exceed reasonable limits."""
    return content[:max_length] if len(content) > max_length else content


def validate_url(url: str) -> bool:
    """Basic URL validation — returns True if the string is a plausible URL."""
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except Exception:
        return False


def validate_ttl(ttl: int, max_ttl: int = 2592000) -> int:
    """Validate and clamp TTL values."""
    if ttl < 0:
        return 0
    if ttl > max_ttl:
        return max_ttl
    return ttl


def utcnow() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    """Format a datetime as ISO 8601 UTC string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _pad_b64(s: str) -> str:
    """Add correct base64 padding."""
    return s + "=" * ((4 - len(s) % 4) % 4)
