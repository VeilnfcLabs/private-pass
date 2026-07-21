"""Cryptographic utilities for VeilPass API.

Supports Ed25519 signing/verification, HMAC-SHA256, JWT creation/verification,
nonce generation, and timestamp validation.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.config import settings

# ── Ed25519 helpers ────────────────────────────────────────────────────────────


def _load_signing_key() -> Optional[ed25519.Ed25519PrivateKey]:
    """Load Ed25519 private key from hex-encoded config setting."""
    raw = settings.signing_key
    if not raw:
        return None
    try:
        key_bytes = bytes.fromhex(raw)
        return ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
    except Exception:
        return None


def _load_verification_key() -> Optional[ed25519.Ed25519PublicKey]:
    """Load Ed25519 public key from hex-encoded config setting."""
    raw = settings.verification_key
    if not raw:
        return None
    try:
        key_bytes = bytes.fromhex(raw)
        return ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
    except Exception:
        return None


def generate_ed25519_keypair() -> dict[str, str]:
    """Generate a new Ed25519 keypair and return hex-encoded keys."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return {
        "private_key": private_bytes.hex(),
        "public_key": public_bytes.hex(),
    }


def ed25519_sign(payload: bytes) -> bytes:
    """Sign bytes with the configured Ed25519 private key."""
    key = _load_signing_key()
    if key is None:
        raise ValueError("Ed25519 signing key is not configured")
    return key.sign(payload)


def ed25519_verify(payload: bytes, signature: bytes) -> bool:
    """Verify an Ed25519 signature against the configured public key."""
    key = _load_verification_key()
    if key is None:
        raise ValueError("Ed25519 verification key is not configured")
    try:
        key.verify(signature, payload)
        return True
    except Exception:
        return False


# ── HMAC-SHA256 helpers ───────────────────────────────────────────────────────


def _hmac_key() -> bytes:
    """Derive an HMAC key from the signing key, or use a generated fallback."""
    if settings.signing_key:
        return hashlib.sha256(settings.signing_key.encode()).digest()
    return secrets.token_bytes(32)


def hmac_sign(payload: str) -> str:
    """Create an HMAC-SHA256 signature (hex-encoded)."""
    key = _hmac_key()
    mac = hmac.new(key, payload.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


def hmac_verify(payload: str, signature: str) -> bool:
    """Verify an HMAC-SHA256 signature."""
    expected = hmac_sign(payload)
    return hmac.compare_digest(expected, signature)


# ── JWT helpers ────────────────────────────────────────────────────────────────


def create_jwt(
    payload: dict[str, Any],
    ttl: int = 86400,
    issuer: str = "veilpass",
    audience: str = "",
) -> str:
    """Create a signed JWT using Ed25519 (EdDSA algorithm)."""
    now = int(time.time())
    token_payload = {
        **payload,
        "iat": now,
        "exp": now + ttl,
        "iss": issuer,
    }
    if audience:
        token_payload["aud"] = audience

    key = _load_signing_key()
    if key is None:
        raise ValueError("Ed25519 signing key is not configured for JWT creation")

    return jwt.encode(token_payload, key, algorithm="EdDSA")


def decode_jwt(token: str, audience: str = "") -> dict[str, Any]:
    """Decode and verify a JWT using the configured Ed25519 public key."""
    key = _load_verification_key()
    if key is None:
        raise ValueError("Ed25519 verification key is not configured for JWT verification")

    options = {"verify_exp": True}
    if audience:
        options["verify_aud"] = True

    return jwt.decode(
        token,
        key,
        algorithms=["EdDSA"],
        audience=audience or None,
        options=options,
    )


# ── Nonce ─────────────────────────────────────────────────────────────────────


def generate_nonce() -> str:
    """Generate a cryptographically secure nonce."""
    return secrets.token_urlsafe(32)


# ── Timestamp validation ──────────────────────────────────────────────────────


def validate_timestamp(ts: int, leeway: int = 300) -> bool:
    """Check if a Unix timestamp is within acceptable leeway of now."""
    now = int(time.time())
    return abs(now - ts) <= leeway


def is_expired(expires_at: datetime) -> bool:
    """Check if a datetime is in the past."""
    return datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc)
