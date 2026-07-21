"""NFC payload generation endpoint for VeilPass API."""

import base64
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.crypto import generate_nonce, ed25519_sign, hmac_sign
from app.deps import rate_limit_dependency, request_id_dependency
from app.models.schemas import NFCPayloadRequest, NFCPayloadResponse
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/nfc", tags=["NFC"])


@router.post("", response_model=NFCPayloadResponse, summary="Generate NFC payload")
async def generate_nfc_payload(
    body: NFCPayloadRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate a signed NFC payload with multiple export formats."""
    nfc_id = generate_id()
    nonce = generate_nonce()
    timestamp = format_timestamp(utcnow())

    # Build the payload document
    payload_doc = {
        "id": nfc_id,
        "type": body.type,
        "version": body.version,
        "issuer": body.issuer,
        "timestamp": timestamp,
        "nonce": nonce,
        "payload": body.payload,
        "metadata": body.metadata or {},
    }

    if body.expiration:
        payload_doc["expiration"] = body.expiration

    # Sign the payload
    payload_bytes = json.dumps(payload_doc, separators=(",", ":")).encode("utf-8")

    try:
        signature = ed25519_sign(payload_bytes)
        sig_hex = signature.hex()
        sig_base64 = base64.b64encode(signature).decode("utf-8")
    except ValueError:
        # Fallback to HMAC if Ed25519 not configured
        sig_hex = hmac_sign(payload_bytes.decode("utf-8"))
        sig_base64 = base64.b64encode(sig_hex.encode()).decode("utf-8")
        signature = sig_hex.encode()

    # Export formats
    payload_json = json.dumps(payload_doc, separators=(",", ":"))
    exports = {
        "json": payload_json,
        "hex": payload_bytes.hex(),
        "base64": base64.b64encode(payload_bytes).decode("utf-8"),
        "ndef": base64.b64encode(payload_bytes).decode("utf-8"),  # simplified NDEF wrapper
    }

    # Also include signature in exports
    exports["signature_hex"] = sig_hex
    exports["signature_base64"] = sig_base64

    return NFCPayloadResponse(
        id=nfc_id,
        type=body.type,
        version=body.version,
        issuer=body.issuer,
        timestamp=timestamp,
        nonce=nonce,
        signature=sig_hex,
        payload=body.payload,
        exports=exports,
        request_id=request_id,
    )
