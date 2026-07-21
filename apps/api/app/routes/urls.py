"""Signed URL generation endpoint for VeilPass API."""

import base64
import json
from datetime import timedelta
from urllib.parse import urlencode, urlparse, urlunparse

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.crypto import generate_nonce, ed25519_sign, hmac_sign
from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import SignedURLRequest, SignedURLResponse
from app.utils import generate_id, format_timestamp, utcnow, validate_url, validate_ttl

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/signed-url", tags=["Signed URLs"])


@router.post("", response_model=SignedURLResponse, summary="Create a signed URL")
async def create_signed_url(
    body: SignedURLRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create a signed URL with query parameter authentication."""
    if not validate_url(body.url):
        raise InvalidInputError("Invalid URL provided")

    ttl = validate_ttl(body.expires_in, max_ttl=2592000)
    expires_at = utcnow() + timedelta(seconds=ttl)
    key_id = generate_id()
    nonce = generate_nonce()

    exp_timestamp = int(expires_at.timestamp())

    # Build the signature payload (URL + permissions + expiration)
    sig_payload = json.dumps(
        {
            "url": body.url,
            "permissions": body.permissions,
            "expires": exp_timestamp,
            "key_id": key_id,
            "nonce": nonce,
            "one_time": body.one_time,
            "download_limit": body.download_limit,
        },
        separators=(",", ":"),
    )

    try:
        signature_bytes = ed25519_sign(sig_payload.encode("utf-8"))
        signature = base64.urlsafe_b64encode(signature_bytes).decode("utf-8").rstrip("=")
    except ValueError:
        signature = hmac_sign(sig_payload)

    # Append signature params to the original URL
    parsed = urlparse(body.url)
    query_params = {
        "expires": str(exp_timestamp),
        "signature": signature,
        "key_id": key_id,
    }

    # Preserve existing query params
    existing_params = {}
    if parsed.query:
        for pair in parsed.query.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                existing_params[k] = v

    all_params = {**existing_params, **query_params}
    new_query = urlencode(all_params)

    signed_url = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )

    return SignedURLResponse(
        signed_url=signed_url,
        expires=format_timestamp(expires_at),
        signature=signature,
        key_id=key_id,
        request_id=request_id,
    )
