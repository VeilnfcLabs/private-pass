"""Key management with multi-key support and rotation.

Supports Ed25519 signing key generation, activation/deactivation, scheduled
rotation, and key health monitoring. Multiple keys can co-exist so that older
keys remain available for verifying tokens signed before a rotation.
"""

import hashlib
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.crypto import generate_ed25519_keypair
from app.deps import api_key_dependency, rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError
from app.models.schemas import (
    SigningKeyResponse,
    SigningKeyListResponse,
    RotateKeysRequest,
    RotateKeysResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/keys", tags=["Keys"])

# In-memory key store (use HSM/KMS / database in production)
_signing_keys: dict[str, dict] = {}
_active_key_id: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────────


def _derive_key_id(public_key_hex: str) -> str:
    """Derive a short key identifier from the SHA-256 hash of the public key."""
    return hashlib.sha256(public_key_hex.encode()).hexdigest()[:8]


def _build_key_response(
    key_id: str, data: dict, request_id: str
) -> SigningKeyResponse:
    """Build a ``SigningKeyResponse`` without exposing the private key."""
    return SigningKeyResponse(
        id=key_id,
        key_id=data.get("key_id", ""),
        purpose=data.get("purpose", "general"),
        algorithm=data.get("algorithm", "Ed25519"),
        public_key=data["public_key"],
        created_at=data["created_at"],
        active=data.get("active", False),
        expires_at=data.get("expires_at"),
        tags=data.get("tags", []),
        request_id=request_id,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=SigningKeyResponse,
    summary="Generate a new signing key",
    status_code=201,
)
async def create_signing_key(
    purpose: str = "general",
    algorithm: str = "Ed25519",
    set_active: bool = True,
    tags: list[str] = [],
    _rate: None = Depends(rate_limit_dependency),
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> SigningKeyResponse:
    """Generate a new Ed25519 signing key pair.

    The private key is stored securely in memory and **never** returned in the
    API response. Only the public key and key identifier are exposed.
    """
    if algorithm != "Ed25519":
        raise InvalidInputError(f"Unsupported algorithm: {algorithm}. Use 'Ed25519'.")

    key_id = f"key_{generate_id()}"
    keypair = generate_ed25519_keypair()
    kid = _derive_key_id(keypair["public_key"])
    now = format_timestamp(utcnow())

    # Keys are valid for 90 days by default
    expires_at = format_timestamp(utcnow() + timedelta(days=90))

    _signing_keys[key_id] = {
        "id": key_id,
        "key_id": kid,
        "purpose": purpose,
        "algorithm": "Ed25519",
        "public_key": keypair["public_key"],
        "private_key": keypair["private_key"],  # stored securely; never exposed
        "created_at": now,
        "active": False,
        "expires_at": expires_at,
        "tags": tags,
    }

    global _active_key_id
    if set_active:
        _active_key_id = key_id
        _signing_keys[key_id]["active"] = True

    logger.info(
        "signing_key_created",
        key_id=key_id,
        kid=kid,
        purpose=purpose,
        set_active=set_active,
    )

    return _build_key_response(key_id, _signing_keys[key_id], request_id)


@router.get(
    "",
    response_model=SigningKeyListResponse,
    summary="List all signing keys",
)
async def list_signing_keys(
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> SigningKeyListResponse:
    """Return all signing keys (public info only).

    Keys are sorted by creation date descending. The currently active key is
    indicated by ``active_key_id``.
    """
    keys = [
        _build_key_response(kid, data, request_id)
        for kid, data in sorted(
            _signing_keys.items(),
            key=lambda item: item[1].get("created_at", ""),
            reverse=True,
        )
    ]

    return SigningKeyListResponse(
        keys=keys,
        total=len(keys),
        active_key_id=_active_key_id,
        request_id=request_id,
    )


@router.get(
    "/active",
    response_model=SigningKeyResponse,
    summary="Get the current active signing key",
)
async def get_active_key(
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> SigningKeyResponse:
    """Return public information about the currently active signing key."""
    if _active_key_id is None or _active_key_id not in _signing_keys:
        raise NotFoundError("No active signing key found")

    return _build_key_response(
        _active_key_id, _signing_keys[_active_key_id], request_id
    )


@router.get(
    "/status",
    summary="Key health and status overview",
)
async def key_status(
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> dict:
    """Return key health metrics: active key age, total count, rotation info."""
    now = utcnow()
    active_key_age_seconds = 0
    active_key_id = _active_key_id

    if _active_key_id and _active_key_id in _signing_keys:
        created = _signing_keys[_active_key_id].get("created_at", "")
        if created:
            try:
                created_dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
                active_key_age_seconds = int((now - created_dt).total_seconds())
            except ValueError:
                pass

    # Count keys expiring within 7 days
    warning_threshold = now + timedelta(days=7)
    keys_expiring_soon = 0
    for data in _signing_keys.values():
        expires = data.get("expires_at")
        if expires:
            try:
                expires_dt = datetime.strptime(
                    expires, "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=timezone.utc)
                if expires_dt <= warning_threshold:
                    keys_expiring_soon += 1
            except ValueError:
                pass

    return {
        "success": True,
        "active_key_id": active_key_id,
        "active_key_age_seconds": active_key_age_seconds,
        "active_key_age_hours": round(active_key_age_seconds / 3600, 1),
        "total_keys": len(_signing_keys),
        "active_keys": sum(
            1 for d in _signing_keys.values() if d.get("active")
        ),
        "keys_expiring_soon": keys_expiring_soon,
        "next_rotation_due_days": max(0, 90 - (active_key_age_seconds // 86400))
        if active_key_age_seconds
        else 0,
        "request_id": request_id,
    }


@router.get(
    "/{key_id}",
    response_model=SigningKeyResponse,
    summary="Get signing key details",
)
async def get_signing_key(
    key_id: str,
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> SigningKeyResponse:
    """Return public information about a specific signing key."""
    data = _signing_keys.get(key_id)
    if data is None:
        raise NotFoundError(f"Signing key not found: {key_id}")

    return _build_key_response(key_id, data, request_id)


@router.post(
    "/{key_id}/activate",
    response_model=SigningKeyResponse,
    summary="Activate a signing key",
)
async def activate_signing_key(
    key_id: str,
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> SigningKeyResponse:
    """Set a specific key as the active signing key.

    The previously active key remains available for verification of existing
    tokens but will no longer be used for new signatures.
    """
    if key_id not in _signing_keys:
        raise NotFoundError(f"Signing key not found: {key_id}")

    # Deactivate all keys
    for k in _signing_keys:
        _signing_keys[k]["active"] = False

    global _active_key_id
    _active_key_id = key_id
    _signing_keys[key_id]["active"] = True
    _signing_keys[key_id]["activated_at"] = format_timestamp(utcnow())

    logger.info("signing_key_activated", key_id=key_id)

    return _build_key_response(key_id, _signing_keys[key_id], request_id)


@router.post(
    "/{key_id}/deactivate",
    response_model=SigningKeyResponse,
    summary="Deactivate a signing key",
)
async def deactivate_signing_key(
    key_id: str,
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> SigningKeyResponse:
    """Deactivate a signing key.

    The key remains in the store so existing signatures can still be verified,
    but it will no longer be used for signing new tokens.
    """
    if key_id not in _signing_keys:
        raise NotFoundError(f"Signing key not found: {key_id}")

    _signing_keys[key_id]["active"] = False

    global _active_key_id
    if _active_key_id == key_id:
        _active_key_id = None

    logger.info("signing_key_deactivated", key_id=key_id)

    return _build_key_response(key_id, _signing_keys[key_id], request_id)


@router.post(
    "/rotate",
    response_model=RotateKeysResponse,
    summary="Rotate the active signing key",
)
async def rotate_signing_key(
    body: RotateKeysRequest,
    _rate: None = Depends(rate_limit_dependency),
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> RotateKeysResponse:
    """Rotate the active signing key.

    * The current active key is deactivated but kept in the store so that
      tokens signed with it can still be verified.
    * A brand-new key is generated and set as the active signing key.
    * The rotation event is logged for audit purposes.
    """
    global _active_key_id

    previous_key_id = _active_key_id

    if previous_key_id and previous_key_id in _signing_keys:
        _signing_keys[previous_key_id]["active"] = False
        _signing_keys[previous_key_id]["rotated_at"] = format_timestamp(utcnow())
        _signing_keys[previous_key_id]["rotation_reason"] = body.reason
        logger.info(
            "signing_key_deactivated_for_rotation",
            key_id=previous_key_id,
            reason=body.reason,
        )

    # Generate new key
    new_key_id = f"key_{generate_id()}"
    keypair = generate_ed25519_keypair()
    kid = _derive_key_id(keypair["public_key"])
    now = format_timestamp(utcnow())
    expires_at = format_timestamp(utcnow() + timedelta(days=90))

    _signing_keys[new_key_id] = {
        "id": new_key_id,
        "key_id": kid,
        "purpose": "general",
        "algorithm": "Ed25519",
        "public_key": keypair["public_key"],
        "private_key": keypair["private_key"],
        "created_at": now,
        "active": True,
        "expires_at": expires_at,
        "tags": [],
        "rotation_reason": body.reason,
    }

    _active_key_id = new_key_id

    logger.info(
        "signing_key_rotated",
        new_key_id=new_key_id,
        previous_key_id=previous_key_id,
        reason=body.reason,
    )

    return RotateKeysResponse(
        new_key_id=new_key_id,
        previous_key_id=previous_key_id or "",
        rotated_at=now,
        request_id=request_id,
    )


# ── Crypto helpers for other modules ───────────────────────────────────────────


def get_active_private_key() -> Optional[bytes]:
    """Return the private key bytes of the currently active signing key.

    Used internally by the crypto module to sign tokens.
    Returns ``None`` if no active key is available.
    """
    if _active_key_id is None or _active_key_id not in _signing_keys:
        return None
    priv_hex = _signing_keys[_active_key_id].get("private_key")
    if priv_hex is None:
        return None
    return bytes.fromhex(priv_hex)


def get_verification_keys() -> list[dict[str, str]]:
    """Return all available public keys for signature verification.

    Returns a list of dicts with ``key_id`` and ``public_key`` (hex-encoded).
    """
    keys = []
    for kid, data in _signing_keys.items():
        keys.append(
            {
                "key_id": data.get("key_id", ""),
                "public_key": data["public_key"],
                "active": data.get("active", False),
            }
        )
    return keys


def get_key_by_id(key_id: str) -> Optional[dict]:
    """Return the full key record for a given key ID (key_*)."""
    return _signing_keys.get(key_id)


def get_key_by_kid(kid: str) -> Optional[dict]:
    """Return the first key record matching a short key identifier (a1b2c3d4)."""
    for data in _signing_keys.values():
        if data.get("key_id") == kid:
            return data
    return None
