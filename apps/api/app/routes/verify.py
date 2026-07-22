"""Verification endpoint for VeilPass API.

Supports verification of tokens, signed-links, signed-urls,
and SD-JWT (Selective Disclosure JWT) presentations.
"""

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from structlog import get_logger

from app.crypto import decode_jwt, ed25519_verify, hmac_verify, is_expired, validate_timestamp
from app.deps import request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import (
    SDJWTVeirfyResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.routes.revoke import is_revoked
from app.sdjwt import verify_sd_jwt
from app.utils import _pad_b64

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/verify", tags=["Verification"])


# ── Token identifier helpers ─────────────────────────────────────────


def _token_fingerprint(token: str) -> str:
    """Derive a stable identifier from a JWT for revocation lookups."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]


def _check_revocation(token: str) -> None:
    """Raise InvalidInputError if the token has been revoked."""
    if is_revoked(_token_fingerprint(token)):
        raise InvalidInputError("Token has been revoked")


# ── Internal verifiers ───────────────────────────────────────────────


def _verify_token(value: str) -> dict:
    """Verify a JWT token and return claims."""
    _check_revocation(value)
    try:
        # Try Ed25519/EdDSA JWT verification
        decoded = decode_jwt(value)
        return {
            "valid": True,
            "expired": False,
            "issuer": decoded.get("iss", ""),
            "signature_valid": True,
            "claims": decoded,
        }
    except Exception as jwt_err:
        logger.warning("jwt_verification_failed", error=str(jwt_err))
        return {
            "valid": False,
            "expired": "expired" in str(jwt_err).lower(),
            "issuer": "",
            "signature_valid": False,
            "claims": {},
        }


def _verify_signed_link(value: str) -> dict:
    """Verify a signed-link token (payload.signature format)."""
    parts = value.split(".")
    if len(parts) != 2:
        return {
            "valid": False,
            "expired": False,
            "issuer": "veilpass",
            "signature_valid": False,
            "claims": {},
        }

    payload_b64, sig_b64 = parts
    try:
        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(_pad_b64(payload_b64))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return {
            "valid": False,
            "expired": False,
            "issuer": "veilpass",
            "signature_valid": False,
            "claims": {},
        }

    # Verify signature — try Ed25519 first, fall back to HMAC
    signature_valid = False
    try:
        sig_bytes = base64.urlsafe_b64decode(_pad_b64(sig_b64))
        signature_valid = ed25519_verify(payload_bytes, sig_bytes)
    except Exception:
        try:
            signature_valid = hmac_verify(payload_bytes.decode("utf-8"), sig_b64)
        except Exception:
            signature_valid = False

    # Check expiration
    expired = False
    exp_str = payload.get("exp", "")
    if exp_str:
        try:
            exp_dt = datetime.fromisoformat(exp_str)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            expired = datetime.now(timezone.utc) > exp_dt
        except (ValueError, TypeError):
            pass

    return {
        "valid": signature_valid and not expired,
        "expired": expired,
        "issuer": payload.get("issuer", "veilpass"),
        "signature_valid": signature_valid,
        "claims": payload,
    }


def _verify_signed_url(value: str) -> dict:
    """Verify a signed URL by checking its query parameters."""
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(value)
    params = parse_qs(parsed.query)

    expires = params.get("expires", [None])[0]
    signature = params.get("signature", [None])[0]
    key_id = params.get("key_id", [None])[0]

    if not expires or not signature:
        return {
            "valid": False,
            "expired": False,
            "issuer": "veilpass",
            "signature_valid": False,
            "claims": {},
        }

    # Check expiration
    try:
        exp_ts = int(expires)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        expired = now_ts > exp_ts
    except (ValueError, TypeError):
        expired = False

    # Reconstruct the expected signature payload
    sig_payload = json.dumps(
        {
            "url": value,
            "expires": expires,
            "key_id": key_id,
        },
        separators=(",", ":"),
    )

    signature_valid = False
    try:
        sig_bytes = base64.urlsafe_b64decode(_pad_b64(signature))
        signature_valid = ed25519_verify(sig_payload.encode("utf-8"), sig_bytes)
    except Exception:
        try:
            signature_valid = hmac_verify(sig_payload, signature)
        except Exception:
            signature_valid = False

    return {
        "valid": signature_valid and not expired,
        "expired": expired,
        "issuer": "veilpass",
        "signature_valid": signature_valid,
        "claims": {"key_id": key_id, "expires": expires},
    }


# ── Standard verification endpoints ──────────────────────────────────


@router.post("", response_model=VerifyResponse, summary="Verify a token, signed-link, or signed-url")
async def verify_post(
    body: VerifyRequest,
    request_id: str = Depends(request_id_dependency),
):
    """Verify the validity of a token, signed-link, or signed-url."""
    if body.type == "token":
        result = _verify_token(body.value)
    elif body.type == "signed-link":
        result = _verify_signed_link(body.value)
    elif body.type == "signed-url":
        result = _verify_signed_url(body.value)
    else:
        raise InvalidInputError(f"Unsupported verification type: {body.type}")

    return VerifyResponse(
        valid=result["valid"],
        expired=result["expired"],
        issuer=result["issuer"],
        signature_valid=result["signature_valid"],
        claims=result["claims"],
        request_id=request_id,
    )


@router.get("", response_model=VerifyResponse, summary="Verify via query parameters")
async def verify_get(
    type: str = Query(..., pattern=r"^(token|signed-link|signed-url)$"),
    value: str = Query(..., max_length=8192),
    request_id: str = Depends(request_id_dependency),
):
    """Verify a token, signed-link, or signed-url via GET query parameters."""
    return await verify_post(
        body=VerifyRequest(type=type, value=value),
        request_id=request_id,
    )


# ── SD-JWT Verification ──────────────────────────────────────────────


class SDJWTVeirfyRequest(BaseModel):
    """Request model for SD-JWT verification."""

    token: str
    disclosures: list[str]


@router.post(
    "/sd-jwt",
    response_model=SDJWTVeirfyResponse,
    summary="Verify an SD-JWT presentation",
)
async def verify_sd_jwt_endpoint(
    body: SDJWTVeirfyRequest,
    request_id: str = Depends(request_id_dependency),
):
    """Verify an SD-JWT and return the disclosed claims.

    Provide the SD-JWT token and the disclosures the holder is presenting.
    The server verifies:
      1. The JWT signature (Ed25519/EdDSA)
      2. Token expiration
      3. Revocation status
      4. Each disclosure digest matches the embedded digest in the JWT

    On success, returns the verified disclosed claims.
    """
    if not body.token.strip():
        raise InvalidInputError("Token cannot be empty")

    if not body.disclosures:
        raise InvalidInputError("Disclosures list cannot be empty")

    # Check revocation
    _check_revocation(body.token)

    try:
        disclosed_claims = verify_sd_jwt(
            token=body.token,
            disclosures=body.disclosures,
        )
        return SDJWTVeirfyResponse(
            valid=True,
            expired=False,
            disclosed_claims=disclosed_claims,
            request_id=request_id,
        )
    except Exception as exc:
        err_str = str(exc).lower()
        is_expired = "expired" in err_str
        return SDJWTVeirfyResponse(
            valid=False,
            expired=is_expired,
            disclosed_claims={},
            request_id=request_id,
        )
