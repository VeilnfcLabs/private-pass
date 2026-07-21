"""Token generation endpoint for VeilPass API."""

import base64
import json
from datetime import timedelta

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.crypto import create_jwt, ed25519_sign, hmac_sign
from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import TokenRequest, TokenResponse
from app.utils import format_timestamp, utcnow, validate_ttl

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
        padded = s + "=" * (4 - len(s) % 4) if len(s) % 4 else s
        try:
            return json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
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
