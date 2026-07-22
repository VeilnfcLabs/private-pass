"""Hybrid NFC + QR encrypted payloads. Encrypt once, output both formats.

Encrypts a payload with AES-256-GCM and exports the result as NFC NDEF
payloads (hex/base64/ndef) and QR code images (PNG/SVG).  A single
user-chosen password protects the data; the same password is required
for decryption.

Key derivation: SHA-256(password) → 256-bit AES key.
"""

import base64
import hashlib
import io
import os
from typing import Optional

import qrcode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import APIRouter, Depends
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import (
    DecryptPayloadRequest,
    DecryptPayloadResponse,
    EncryptedData,
    EncryptedPayloadRequest,
    EncryptedPayloadResponse,
    NFCFromEncryptedRequest,
    NFCFromEncryptedResponse,
    NFCPayloadContainer,
    QRFromEncryptedRequest,
    QRFromEncryptedResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/encrypted", tags=["Encrypted Payloads"])

# ECL mapping
_ECL_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


# ── Core encryption helpers ────────────────────────────────────────────────────


def encrypt_payload(plaintext: str, password: str) -> EncryptedData:
    """Encrypt *plaintext* with AES-256-GCM.

    Key derivation: SHA-256(password).

    Returns a fully-populated :class:`EncryptedData` with base64-encoded
    *ciphertext*, *nonce* and *tag*.
    """
    key = hashlib.sha256(password.encode()).digest()
    nonce = os.urandom(12)  # 96-bit nonce for GCM

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()

    return EncryptedData(
        ciphertext=base64.b64encode(ciphertext).decode(),
        nonce=base64.b64encode(nonce).decode(),
        tag=base64.b64encode(encryptor.tag).decode(),
        algorithm="AES-256-GCM",
        kdf="SHA-256",
    )


def decrypt_payload(encrypted: EncryptedData, password: str) -> str:
    """Decrypt an AES-256-GCM encrypted payload.

    Raises :class:`InvalidInputError` if the password is wrong or the
    ciphertext has been tampered with (GCM authentication failure).
    """
    key = hashlib.sha256(password.encode()).digest()
    try:
        ciphertext = base64.b64decode(encrypted.ciphertext)
        nonce = base64.b64decode(encrypted.nonce)
        tag = base64.b64decode(encrypted.tag)
    except Exception as exc:
        raise InvalidInputError(f"Invalid base64 data: {exc}")

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
    decryptor = cipher.decryptor()
    try:
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    except Exception as exc:
        raise InvalidInputError(
            "Decryption failed — incorrect password or corrupted data"
        ) from exc

    return plaintext.decode()


def _build_nfc_payload(encrypted: EncryptedData, nfc_type: str = "uri") -> NFCPayloadContainer:
    """Build NFC NDEF payload containers from encrypted data.

    The payload data is serialized as JSON and exported as hex, base64,
    and a simplified NDEF wrapper.
    """
    import json as _json

    payload_doc = {
        "type": nfc_type,
        "algorithm": encrypted.algorithm,
        "kdf": encrypted.kdf,
        "ciphertext": encrypted.ciphertext,
        "nonce": encrypted.nonce,
        "tag": encrypted.tag,
    }

    payload_bytes = _json.dumps(payload_doc, separators=(",", ":")).encode("utf-8")

    return NFCPayloadContainer(
        hex=payload_bytes.hex(),
        base64=base64.b64encode(payload_bytes).decode("utf-8"),
        ndef=base64.b64encode(payload_bytes).decode("utf-8"),  # simplified NDEF
    )


def _build_qr_image(encrypted: EncryptedData, qr_format: str = "png") -> str:
    """Generate a QR code image from the encrypted payload metadata.

    The QR content is a compact JSON document containing the ciphertext,
    nonce and tag so that scanning the QR + providing the password is
    sufficient to decrypt.

    Returns a base64-encoded image string (PNG or SVG).
    """
    import json as _json

    qr_content = _json.dumps(
        {
            "v": 1,
            "alg": encrypted.algorithm,
            "kdf": encrypted.kdf,
            "ct": encrypted.ciphertext,
            "n": encrypted.nonce,
            "t": encrypted.tag,
        },
        separators=(",", ":"),
    )

    if qr_format == "svg":
        # SVG path — use qrcode's native SVG image factory
        import xml.etree.ElementTree as _ET

        svg_factory = qrcode.image.svg.SvgImage
        svg_img = qrcode.make(qr_content, image_factory=svg_factory)
        buffer = io.BytesIO()
        svg_img.save(buffer)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    # PNG path — use PIL
    ecl = _ECL_MAP.get("H", qrcode.constants.ERROR_CORRECT_H)
    qr = qrcode.QRCode(version=None, error_correction=ecl, box_size=10, border=4)
    qr.add_data(qr_content)
    try:
        qr.make(fit=True)
    except ValueError as e:
        raise InvalidInputError(f"Failed to generate QR code: {e}") from e

    img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
    img = img.resize((512, 512))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "/generate",
    response_model=EncryptedPayloadResponse,
    summary="Generate encrypted NFC + QR payload",
)
async def generate_encrypted_payload(
    body: EncryptedPayloadRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Encrypt a payload with AES-256-GCM and output NFC + QR formats.

    The same password is required for decryption.  The response includes
    the encrypted blob, an NFC NDEF container (hex/base64/ndef), and a
    base64-encoded QR code image (PNG or SVG).
    """
    if not body.payload.strip():
        raise InvalidInputError("payload cannot be empty")
    if len(body.password) < 4:
        raise InvalidInputError("password must be at least 4 characters")

    enc_id = f"enc_{generate_id()}"
    created_at = format_timestamp(utcnow())

    # Encrypt
    encrypted = encrypt_payload(body.payload, body.password)

    # Build output formats
    nfc_payload: Optional[NFCPayloadContainer] = None
    qr_data: Optional[str] = None

    if body.output_format in ("both", "nfc"):
        nfc_payload = _build_nfc_payload(encrypted, body.nfc_type)

    if body.output_format in ("both", "qr"):
        qr_data = _build_qr_image(encrypted, body.qr_format)

    logger.info(
        "encrypted_payload_generated",
        id=enc_id,
        output_format=body.output_format,
    )

    return EncryptedPayloadResponse(
        id=enc_id,
        encrypted=encrypted,
        nfc_payload=nfc_payload,
        qr_data=qr_data,
        decryption_key_hint="SHA-256(password)",
        created_at=created_at,
        request_id=request_id,
    )


@router.post(
    "/decrypt",
    response_model=DecryptPayloadResponse,
    summary="Decrypt an encrypted payload",
)
async def decrypt_encrypted_payload(
    body: DecryptPayloadRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Decrypt a payload with the user-chosen password.

    Returns the original plaintext on success.  If the password is
    incorrect or the ciphertext has been tampered with, the endpoint
    returns a 400 error.
    """
    plaintext = decrypt_payload(body.encrypted, body.password)

    logger.info("encrypted_payload_decrypted", algorithm=body.encrypted.algorithm)

    return DecryptPayloadResponse(
        plaintext=plaintext,
        algorithm=body.encrypted.algorithm,
        request_id=request_id,
    )


@router.post(
    "/nfc",
    response_model=NFCFromEncryptedResponse,
    summary="Generate NFC payload from encrypted data",
)
async def generate_nfc_from_encrypted(
    body: NFCFromEncryptedRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Convert an existing encrypted payload into NFC NDEF container formats."""
    nfc_payload = _build_nfc_payload(body.encrypted, body.nfc_type)

    return NFCFromEncryptedResponse(
        nfc_payload=nfc_payload,
        request_id=request_id,
    )


@router.post(
    "/qr",
    response_model=QRFromEncryptedResponse,
    summary="Generate QR code from encrypted data",
)
async def generate_qr_from_encrypted(
    body: QRFromEncryptedRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate a QR code image (base64) from an existing encrypted payload."""
    qr_data = _build_qr_image(body.encrypted, body.qr_format)

    return QRFromEncryptedResponse(
        qr_data=qr_data,
        request_id=request_id,
    )
