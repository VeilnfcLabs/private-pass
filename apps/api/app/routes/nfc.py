"""NFC payload generation and anti-cloning UID binding for VeilPass API.

Generates signed NFC payloads with multiple export formats (hex, base64,
NDEF).  When UID binding is enabled, the NFC tag's unique identifier is
embedded in the signed payload so the credential cannot be copied to
another tag.
"""

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.crypto import generate_nonce, ed25519_sign, ed25519_verify, hmac_sign, hmac_verify
from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import (
    NFCPayloadRequest,
    NFCPayloadResponse,
    NFCUidVerifyRequest,
    NFCUidVerifyResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/nfc", tags=["NFC"])


def _sign_payload_bytes(payload_bytes: bytes) -> tuple[bytes, str, str]:
    """Sign *payload_bytes* with Ed25519 (fallback HMAC-SHA256).

    Returns:
        Tuple of ``(signature_bytes, sig_hex, sig_base64)``.
    """
    try:
        signature = ed25519_sign(payload_bytes)
        sig_hex = signature.hex()
        sig_base64 = base64.b64encode(signature).decode("utf-8")
        return signature, sig_hex, sig_base64
    except ValueError:
        # Fallback to HMAC if Ed25519 not configured
        sig_hex = hmac_sign(payload_bytes.decode("utf-8"))
        sig_base64 = base64.b64encode(sig_hex.encode()).decode("utf-8")
        return sig_hex.encode(), sig_hex, sig_base64


def _build_payload_doc(
    body: NFCPayloadRequest,
    nfc_id: str,
    nonce: str,
    timestamp: str,
) -> dict[str, Any]:
    """Build the signed payload document, optionally including UID binding."""
    payload_doc: dict[str, Any] = {
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

    # ── Anti-cloning UID binding ─────────────────────────────────────
    bind_to_uid = getattr(body, "bind_to_uid", False)
    uid = getattr(body, "uid", None)

    if bind_to_uid:
        if not uid or not uid.strip():
            raise InvalidInputError(
                "uid is required when bind_to_uid is True. "
                "Provide the NFC tag UID (e.g. 04:12:34:56:78:9A:BC)."
            )
        # Normalise UID: strip whitespace, uppercase hex
        uid_clean = uid.strip().upper()
        payload_doc["uid"] = uid_clean
        payload_doc["uid_locked"] = True

    return payload_doc


# ── Generate NFC Payload ────────────────────────────────────────────────────


@router.post(
    "",
    response_model=NFCPayloadResponse,
    summary="Generate NFC payload (with optional UID binding)",
)
async def generate_nfc_payload(
    body: NFCPayloadRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate a signed NFC payload with multiple export formats.

    When ``bind_to_uid`` is ``True`` and ``uid`` is provided, the NFC
    tag's unique identifier is embedded in the signed payload.  This
    prevents the credential from being cloned to a different tag.

    Supported export formats: ``json``, ``hex``, ``base64``, ``ndef``.
    """
    nfc_id = generate_id()
    nonce = generate_nonce()
    timestamp = format_timestamp(utcnow())

    # Build the payload document (with optional UID binding)
    payload_doc = _build_payload_doc(body, nfc_id, nonce, timestamp)

    uid = payload_doc.get("uid")
    uid_locked = payload_doc.get("uid_locked", False)

    # Sign the serialised payload
    payload_bytes = json.dumps(payload_doc, separators=(",", ":")).encode("utf-8")
    signature, sig_hex, sig_base64 = _sign_payload_bytes(payload_bytes)

    # Export formats
    payload_json = json.dumps(payload_doc, separators=(",", ":"))
    exports: dict[str, str] = {
        "json": payload_json,
        "hex": payload_bytes.hex(),
        "base64": base64.b64encode(payload_bytes).decode("utf-8"),
        "ndef": base64.b64encode(payload_bytes).decode("utf-8"),  # simplified NDEF
        "signature_hex": sig_hex,
        "signature_base64": sig_base64,
    }

    # Include UID binding info in exports when active
    if uid:
        exports["uid"] = uid
        exports["uid_locked"] = "true"
        exports["uid_included_in_signature"] = "true"

    logger.info(
        "nfc_payload_generated",
        nfc_id=nfc_id,
        uid_bound=bool(uid),
    )

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


# ── Verify UID Binding ──────────────────────────────────────────────────────


@router.post(
    "/verify-uid",
    response_model=NFCUidVerifyResponse,
    summary="Verify NFC payload matches a specific UID",
)
async def verify_nfc_uid(
    body: NFCUidVerifyRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Verify that an NFC payload was bound to a specific tag UID.

    Checks:
    1. The payload contains a ``uid`` field.
    2. The payload's ``uid`` matches the provided UID.
    3. The payload signature is valid (if signing keys are configured).
    """
    payload = body.payload
    provided_uid = body.uid.strip().upper()

    # Check if uid is in the payload
    uid_in_payload = "uid" in payload
    uid_match = payload.get("uid", "").upper() == provided_uid if uid_in_payload else False

    # Verify the signature (if the payload has the required fields)
    signature_valid = False
    if "id" in payload and ("signature" in body.payload or True):
        # Reconstruct the signed payload bytes
        sig_fields = ["id", "type", "version", "issuer", "timestamp", "nonce", "payload"]
        has_all_fields = all(f in payload for f in sig_fields)

        if has_all_fields:
            try:
                # Re-serialise in canonical form
                doc_for_verify = {k: payload[k] for k in payload if k in sig_fields or k in ("uid", "uid_locked", "expiration", "metadata")}
                if "uid" in payload:
                    doc_for_verify["uid"] = payload["uid"]
                if "uid_locked" in payload:
                    doc_for_verify["uid_locked"] = payload["uid_locked"]
                if "expiration" in payload:
                    doc_for_verify["expiration"] = payload["expiration"]
                if "metadata" in payload:
                    doc_for_verify["metadata"] = payload["metadata"]

                verify_bytes = json.dumps(doc_for_verify, separators=(",", ":")).encode("utf-8")

                # Try Ed25519 first
                try:
                    sig_bytes = bytes.fromhex(payload.get("signature", ""))
                    signature_valid = ed25519_verify(verify_bytes, sig_bytes)
                except (ValueError, KeyError):
                    pass

                if not signature_valid:
                    # Try HMAC fallback
                    sig_str = payload.get("signature", "")
                    signature_valid = hmac_verify(verify_bytes.decode("utf-8"), sig_str)

            except Exception as exc:
                logger.warning("uid_verify_signature_check_failed", error=str(exc))
                signature_valid = False

    return NFCUidVerifyResponse(
        uid_match=uid_match,
        signature_valid=signature_valid,
        uid_in_payload=uid_in_payload,
        request_id=request_id,
    )
