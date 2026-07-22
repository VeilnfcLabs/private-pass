"""Token generation endpoint for VeilPass API.

Supports standard JWT tokens, SD-JWT selective disclosure tokens,
and revocation checks during verification.
"""

import base64
import hashlib
import json
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.crypto import create_jwt, ed25519_sign, hmac_sign
from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import (
    SDJWTPresentRequest,
    SDJWTPresentResponse,
    SDJWTRequest,
    SDJWTResponse,
    TokenRequest,
    TokenResponse,
)
from app.routes.revoke import is_revoked
from app.sdjwt import create_sd_jwt, present_sd_jwt
from app.utils import _pad_b64, format_timestamp, utcnow, validate_ttl

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/token", tags=["Tokens"])


@router.post("", response_model=TokenResponse, summary="Generate a signed token")
async def create_token(
    body: TokenRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate a JWT token signed with Ed25519."""
    if not body.subject.strip():
        raise InvalidInputError("Subject cannot be empty")

    ttl = validate_ttl(body.expires_in)
    expires_at = utcnow() + timedelta(seconds=ttl)

    # Build JWT claims
    jwt_claims = {
        "sub": body.subject,
        "aud": body.audience,
        "iss": body.issuer,
        **body.claims,
    }

    try:
        token = create_jwt(
            payload=jwt_claims,
            ttl=ttl,
            issuer=body.issuer,
            audience=body.audience,
        )
    except ValueError as exc:
        raise InvalidInputError(str(exc))

    # Decode the token parts for the response
    parts = token.split(".")
    header_b64 = parts[0] if len(parts) > 0 else ""
    payload_b64 = parts[1] if len(parts) > 1 else ""

    # Decode header and payload for inspection
    def _b64_decode(s: str) -> dict:
        try:
            return json.loads(base64.urlsafe_b64decode(_pad_b64(s)).decode("utf-8"))
        except Exception:
            return {}

    decoded_header = _b64_decode(header_b64) if header_b64 else {}
    decoded_payload = _b64_decode(payload_b64) if payload_b64 else {}

    decoded = {
        "header": decoded_header,
        "payload": decoded_payload,
    }

    # For the response signature, use the raw Ed25519 signature from the JWT
    # The JWT itself is the third part
    signature = parts[2] if len(parts) > 2 else ""

    return TokenResponse(
        token=token,
        decoded=decoded,
        signature=signature,
        expires_at=format_timestamp(expires_at),
        request_id=request_id,
    )


# ── SD-JWT: Create ───────────────────────────────────────────────────


@router.post(
    "/sd-jwt",
    response_model=SDJWTResponse,
    summary="Create an SD-JWT with selective disclosure digests",
)
async def create_sd_jwt_endpoint(
    body: SDJWTRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create a Selective Disclosure JWT (SD-JWT).

    The request specifies which claims can be selectively disclosed.
    Claims listed in *disclosable_claims* get salted SHA-256 digests
    embedded in the JWT; the corresponding disclosure strings are
    returned separately.  Claims not in *disclosable_claims* are
    embedded directly in the JWT payload.

    The holder later uses the returned disclosures to present only
    the subset of claims they wish to reveal.
    """
    if not body.subject.strip():
        raise InvalidInputError("Subject cannot be empty")

    ttl = validate_ttl(body.expires_in)
    expires_at = utcnow() + timedelta(seconds=ttl)

    # Merge subject into claims for the SD-JWT payload
    sd_claims: dict[str, Any] = {"sub": body.subject, **body.claims}

    # If disclosable_claims is None → all claims become disclosable
    # If disclosable_claims is [] → no claims are disclosable (all direct)
    if body.disclosable_claims is None:
        disclosable = list(body.claims.keys())
    else:
        disclosable = body.disclosable_claims

    try:
        token, disclosures = create_sd_jwt(
            claims=sd_claims,
            ttl=ttl,
            issuer=body.issuer,
            audience=body.audience,
            disclosable_claims=disclosable,
        )
    except ValueError as exc:
        raise InvalidInputError(str(exc))

    return SDJWTResponse(
        token=token,
        disclosures=disclosures,
        disclosable_claims=disclosable,
        expires_at=format_timestamp(expires_at),
        request_id=request_id,
    )


# ── SD-JWT: Present ──────────────────────────────────────────────────


@router.post(
    "/sd-jwt/present",
    response_model=SDJWTPresentResponse,
    summary="Selectively disclose claims from an SD-JWT",
)
async def present_sd_jwt_endpoint(
    body: SDJWTPresentRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Selectively disclose claims from an SD-JWT.

    Provide the original token, the full set of disclosures, and the
    subset of claims you want to reveal.  Returns a presentation
    payload with only the requested disclosures.
    """
    if not body.token.strip():
        raise InvalidInputError("Token cannot be empty")

    if not body.reveal_claims:
        raise InvalidInputError("reveal_claims list cannot be empty")

    # Check revocation status
    # SD-JWT tokens use the JWT itself as the identifier for revocation
    token_id = _token_fingerprint(body.token)
    if is_revoked(token_id):
        raise InvalidInputError("Token has been revoked")

    try:
        filtered_disclosures = present_sd_jwt(
            disclosures=body.disclosures,
            reveal_claims=body.reveal_claims,
        )
    except ValueError as exc:
        raise InvalidInputError(str(exc))

    return SDJWTPresentResponse(
        presentation_token=body.token,
        disclosures=filtered_disclosures,
        disclosed_claims=body.reveal_claims,
        request_id=request_id,
    )


# ── Helpers ──────────────────────────────────────────────────────────


def _token_fingerprint(token: str) -> str:
    """Derive a stable identifier from a JWT for revocation lookups."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]
