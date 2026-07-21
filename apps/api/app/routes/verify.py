"""Verification endpoint for VeilPass API.

Supports verification of tokens, signed-links, and signed-urls.
"""

import base64
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from structlog import get_logger

from app.crypto import decode_jwt, ed25519_verify, hmac_verify, is_expired, validate_timestamp
from app.deps import request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import VerifyRequest, VerifyResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/verify", tags=["Verification"])


def _verify_token(value: str) -> dict:
    """Verify a JWT token and return claims."""
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
        padded_payload = payload_b64 + "=" * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 else payload_b64
        payload_bytes = base64.urlsafe_b64decode(padded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return {
            "valid": False,
            "expired": False,
            "issuer": "veilpass",
            "signature_valid": False,
            "claims": {},
        }

    # Verify signature
    try:
        sig_bytes = base64.urlsafe_b64decode(sig_b64 + "=" * (4 - len(sig_b64) % 4))
        signature_valid = ed25519_verify(payload_bytes, sig_bytes)
    except Exception:
        # Fallback to HMAC verification
        signature_valid = hmac_verify(payload_bytes.decode("utf-8"), sig_b64)

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

    try:
        sig_bytes = base64.urlsafe_b64decode(signature + "=" * (4 - len(signature) % 4))
        signature_valid = ed25519_verify(sig_payload.encode("utf-8"), sig_bytes)
    except Exception:
        signature_valid = hmac_verify(sig_payload, signature)

    return {
        "valid": signature_valid and not expired,
        "expired": expired,
        "issuer": "veilpass",
        "signature_valid": signature_valid,
        "claims": {"key_id": key_id, "expires": expires},
    }


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
