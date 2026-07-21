"""Signed link generation endpoint for VeilPass API."""

import base64
import json
from datetime import timedelta

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.crypto import generate_nonce, ed25519_sign, hmac_sign
from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import SignedLinkRequest, SignedLinkResponse
from app.utils import generate_id, format_timestamp, utcnow, validate_ttl

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/signed-link", tags=["Signed Links"])


@router.post("", response_model=SignedLinkResponse, summary="Create a signed link")
async def create_signed_link(
    body: SignedLinkRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create a cryptographically signed link with expiration and one-time use support."""
    if not body.resource.strip():
        raise InvalidInputError("Resource identifier cannot be empty")

    ttl = validate_ttl(body.ttl)
    expires_at = utcnow() + timedelta(seconds=ttl)
    nonce = generate_nonce()
    link_id = generate_id()

    # Build token payload
    token_payload = {
        "type": "signed-link",
        "resource": body.resource,
        "id": link_id,
        "nonce": nonce,
        "iat": format_timestamp(utcnow()),
        "exp": format_timestamp(expires_at),
        "one_time": body.one_time,
        "max_uses": body.max_uses,
    }

    payload_bytes = json.dumps(token_payload, separators=(",", ":")).encode("utf-8")

    try:
        signature = ed25519_sign(payload_bytes)
        sig_base64 = base64.b64encode(signature).decode("utf-8")
    except ValueError:
        logger.warning("ed25519_not_configured_falling_back_to_hmac")
        sig_base64 = hmac_sign(payload_bytes.decode("utf-8"))

    # Create the token (base64-encoded payload + signature)
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    token = f"{payload_b64}.{sig_base64}"

    # Construct the signed link URL
    url = f"https://claim.veilpass.app/c/{token}"

    return SignedLinkResponse(
        url=url,
        token=token,
        expires_at=format_timestamp(expires_at),
        signature=sig_base64,
        nonce=nonce,
        request_id=request_id,
    )
