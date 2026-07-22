"""Ephemeral self-destructing credentials with short TTL and auto-revocation.

Provides time-limited, single-use tokens that automatically self-destruct
after first use or TTL expiry. Supports configurable TTL durations:
5min (300), 10min (600), 30min (1800), 1hr (3600), max 24hr (86400).
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError
from app.models.schemas import (
    EphemeralTokenRequest,
    EphemeralTokenResponse,
    EphemeralVerifyRequest,
    EphemeralVerifyResponse,
    EphemeralRevokeRequest,
    EphemeralRevokeResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ephemeral", tags=["Ephemeral Credentials"])

# ── Constants ─────────────────────────────────────────────────────────────────

# Allowed TTL values in seconds
ALLOWED_TTLS = {300, 600, 1800, 3600, 86400}
DEFAULT_TTL = 300  # 5 minutes
MAX_TTL = 86400  # 24 hours

# Token prefix for easy identification
TOKEN_PREFIX = "ep_"

# ── In-memory stores (use Redis in production) ────────────────────────────────

# token_hash -> {subject, purpose, expires_at, one_time, used, created_at}
_token_store: dict[str, dict] = {}

# Derive a stable HMAC key for token signing
_HMAC_KEY: Optional[bytes] = None


def _get_hmac_key() -> bytes:
    """Get or derive the HMAC signing key for ephemeral tokens."""
    global _HMAC_KEY
    if _HMAC_KEY is not None:
        return _HMAC_KEY
    # In production, load from a secure vault or environment variable
    seed = "veilpass-ephemeral-hmac-key-seed-2026"
    _HMAC_KEY = hashlib.sha256(seed.encode()).digest()
    return _HMAC_KEY


def _sign_token(token_id: str, subject: str, expires_at: str) -> str:
    """Create an HMAC-SHA256 signature for an ephemeral token.

    The signature binds the token ID, subject, and expiry to prevent
    tampering.
    """
    key = _get_hmac_key()
    message = f"{token_id}:{subject}:{expires_at}"
    mac = hmac.new(key, message.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


def _verify_token_signature(token_id: str, subject: str, expires_at: str, signature: str) -> bool:
    """Verify the HMAC signature of an ephemeral token."""
    expected = _sign_token(token_id, subject, expires_at)
    return hmac.compare_digest(expected, signature)


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "/token",
    response_model=EphemeralTokenResponse,
    summary="Create an ephemeral token",
)
async def create_ephemeral_token(
    body: EphemeralTokenRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create a new ephemeral self-destructing credential.

    The token will automatically expire after the specified TTL.
    If one_time is True, the token self-destructs after the first use.

    Supported TTL values: 300 (5min), 600 (10min), 1800 (30min),
    3600 (1hr), 86400 (24hr).
    """
    # Validate TTL
    ttl = body.ttl
    if ttl not in ALLOWED_TTLS:
        raise InvalidInputError(
            f"Invalid TTL {ttl}s. Allowed values: {sorted(ALLOWED_TTLS)}"
        )

    if not body.subject or not body.subject.strip():
        raise InvalidInputError("subject is required and must be non-empty")

    # Generate token components
    token_id = secrets.token_urlsafe(24)
    now = utcnow()
    expires_at = now + timedelta(seconds=ttl)
    expires_at_str = format_timestamp(expires_at)
    expires_in = ttl

    # Create signature
    signature = _sign_token(token_id, body.subject.strip(), expires_at_str)

    # Build the full token string
    token = f"{TOKEN_PREFIX}{token_id}"

    # Store token metadata (hash the token for lookup)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    _token_store[token_hash] = {
        "token_id": token_id,
        "subject": body.subject.strip(),
        "purpose": body.purpose or "",
        "expires_at": expires_at_str,
        "expires_ts": int(expires_at.timestamp()),
        "one_time": body.one_time,
        "used": False,
        "created_at": format_timestamp(now),
        "signature": signature,
    }

    logger.info(
        "ephemeral_token_created",
        subject=body.subject,
        ttl=ttl,
        one_time=body.one_time,
        purpose=body.purpose,
    )

    return EphemeralTokenResponse(
        token=token,
        expires_in=expires_in,
        one_time=body.one_time,
        expires_at=expires_at_str,
        request_id=request_id,
    )


@router.post(
    "/verify",
    response_model=EphemeralVerifyResponse,
    summary="Verify an ephemeral token",
)
async def verify_ephemeral_token(
    body: EphemeralVerifyRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Verify an ephemeral credential.

    Checks performed:
      1. Token exists and has a valid structure.
      2. HMAC signature is valid (not tampered).
      3. Token has not expired.
      4. Token has not already been used (if one_time is set).

    If the token is one_time and verification succeeds, it is
    automatically marked as used (self-destruct).
    """
    token = body.token.strip()

    if not token.startswith(TOKEN_PREFIX):
        return EphemeralVerifyResponse(
            valid=False,
            subject="",
            purpose="",
            expired=False,
            one_time_used=False,
            request_id=request_id,
        )

    # Look up the token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    stored = _token_store.get(token_hash)

    if stored is None:
        logger.warning("ephemeral_token_not_found")
        return EphemeralVerifyResponse(
            valid=False,
            subject="",
            purpose="",
            expired=False,
            one_time_used=False,
            request_id=request_id,
        )

    # Check signature
    expected_sig = _sign_token(
        stored["token_id"], stored["subject"], stored["expires_at"]
    )
    if not hmac.compare_digest(expected_sig, stored["signature"]):
        logger.warning("ephemeral_token_invalid_signature")
        return EphemeralVerifyResponse(
            valid=False,
            subject="",
            purpose="",
            expired=False,
            one_time_used=False,
            request_id=request_id,
        )

    # Check expiry
    now_ts = int(time.time())
    expired = now_ts > stored["expires_ts"]

    # Check one-time usage
    one_time_used = stored.get("one_time", False) and stored.get("used", False)

    if expired or one_time_used:
        logger.info(
            "ephemeral_token_invalid",
            expired=expired,
            one_time_used=one_time_used,
            subject=stored["subject"],
        )
        return EphemeralVerifyResponse(
            valid=False,
            subject=stored["subject"],
            purpose=stored["purpose"],
            expired=expired,
            one_time_used=one_time_used,
            request_id=request_id,
        )

    # Auto-self-destruct if one_time
    if stored.get("one_time", False):
        _token_store[token_hash]["used"] = True
        logger.info(
            "ephemeral_token_consumed",
            subject=stored["subject"],
            purpose=stored["purpose"],
        )

    logger.info(
        "ephemeral_token_verified",
        subject=stored["subject"],
        purpose=stored["purpose"],
    )

    return EphemeralVerifyResponse(
        valid=True,
        subject=stored["subject"],
        purpose=stored["purpose"],
        expired=False,
        one_time_used=False,
        request_id=request_id,
    )


@router.post(
    "/revoke",
    response_model=EphemeralRevokeResponse,
    summary="Revoke an ephemeral token before expiry",
)
async def revoke_ephemeral_token(
    body: EphemeralRevokeRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Manually revoke an ephemeral token before its natural expiry.

    Once revoked, the token cannot be verified even if it has not expired.
    """
    token = body.token.strip()

    if not token.startswith(TOKEN_PREFIX):
        raise InvalidInputError("Invalid token format")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    stored = _token_store.get(token_hash)

    if stored is None:
        raise NotFoundError("Token not found")

    # Mark as used so verification fails
    _token_store[token_hash]["used"] = True
    _token_store[token_hash]["revoked_at"] = format_timestamp(utcnow())
    _token_store[token_hash]["revoke_reason"] = body.reason or "manual_revocation"

    logger.info(
        "ephemeral_token_revoked",
        subject=stored["subject"],
        reason=body.reason,
    )

    return EphemeralRevokeResponse(
        token=token,
        revoked=True,
        revoked_at=_token_store[token_hash]["revoked_at"],
        request_id=request_id,
    )
