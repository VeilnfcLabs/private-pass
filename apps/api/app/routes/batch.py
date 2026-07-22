"""Batch generation for QR codes, tokens, and links.

Provides endpoints for generating QR codes, tokens, signed links, and
dynamic QR codes in bulk, returning ZIP archives or JSON arrays.
"""

import base64
import csv
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any

import qrcode
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import (
    BatchDynamicQRRequest,
    BatchDynamicQRResponse,
    BatchLinkRequest,
    BatchLinkResponse,
    BatchQRRequest,
    BatchQRResponse,
    BatchStatusResponse,
    BatchTokenRequest,
    BatchTokenResponse,
    DynamicQRResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Batch"])

# ECL mapping
_ECL_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}

_BASE_REDIRECT_DOMAIN = "https://veil.link/r/"

# Reuse the same in-memory store concept for dynamic QR batch
_dynamic_qr_store: dict[str, dict] = {}


def _generate_qr_image_bytes(
    content: str,
    format: str = "png",
    ecl: str = "H",
    size: int = 512,
) -> tuple[bytes, str]:
    """Generate a QR code image and return (bytes, media_type)."""
    if not content.strip():
        raise InvalidInputError("QR content cannot be empty")

    qr_ecl = _ECL_MAP.get(ecl, qrcode.constants.ERROR_CORRECT_H)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qr_ecl,
        box_size=size // 100 if size > 100 else 10,
        border=4,
    )
    qr.add_data(content)
    try:
        qr.make(fit=True)
    except ValueError as e:
        raise InvalidInputError(
            f"QR content too large for the selected parameters: {e}"
        )

    if format == "svg":
        from qrcode.image.svg import SvgPathImage

        img = qr.make_image(image_factory=SvgPathImage, fill_color="#000000", back_color="#FFFFFF")
        buffer = io.BytesIO()
        img.save(buffer)
        return buffer.getvalue(), "image/svg+xml"

    # PNG
    img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
    if size != img.size[0]:
        img = img.resize((size, size))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue(), "image/png"


# ── Batch QR Generation ─────────────────────────────────────────────────────


@router.post(
    "/qr/batch",
    summary="Batch generate QR codes as a ZIP file",
)
async def batch_generate_qr(
    body: BatchQRRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate multiple QR code images in a single ZIP archive.

    Accepts a list of entries with content and optional filename.
    Returns a ZIP file containing all QR images.
    Supports PNG and SVG formats with configurable ECL and size.
    """
    if not body.entries:
        raise InvalidInputError("At least one entry is required")

    if len(body.entries) > 1000:
        raise InvalidInputError("Maximum 1000 entries per batch request")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, entry in enumerate(body.entries):
            filename = entry.filename or f"qr-{idx + 1:04d}"
            ext = "svg" if body.format == "svg" else "png"
            try:
                qr_bytes, _ = _generate_qr_image_bytes(
                    content=entry.content,
                    format=body.format,
                    ecl=body.ecl,
                    size=body.size,
                )
                zf.writestr(f"{filename}.{ext}", qr_bytes)
            except InvalidInputError as e:
                logger.warning("batch_qr_entry_failed", idx=idx, error=str(e))
                # Write error placeholder
                zf.writestr(f"{filename}-ERROR.txt", str(e))

    zip_buffer.seek(0)

    logger.info(
        "batch_qr_generated",
        count=len(body.entries),
        format=body.format,
    )

    return StreamingResponse(
        content=zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=veilpass-qr-batch-{generate_id()[:8]}.zip",
            "X-Request-ID": request_id,
        },
    )


# ── Batch Token Generation ──────────────────────────────────────────────────


@router.post(
    "/token/batch",
    response_model=BatchTokenResponse,
    summary="Batch generate tokens",
)
async def batch_generate_tokens(
    body: BatchTokenRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate multiple signed tokens in a single request.

    Each entry specifies a subject and optional claims.
    Returns a JSON array of generated tokens.
    """
    if not body.entries:
        raise InvalidInputError("At least one entry is required")

    if len(body.entries) > 100:
        raise InvalidInputError("Maximum 100 entries per batch token request")

    from app.crypto import create_jwt, ed25519_sign, hmac_sign
    from app.utils import validate_ttl

    ttl = validate_ttl(body.ttl)
    tokens = []

    for idx, entry in enumerate(body.entries):
        try:
            # Check if signing key is configured; fall back to unsigned token if not
            from app.config import settings as _settings

            if not _settings.signing_key:
                # Generate an unsigned token when no signing key is configured
                import time as _time
                import base64 as _b64
                import json as _json

                now_ts = int(_time.time())
                header = _b64.urlsafe_b64encode(
                    _json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
                ).decode().rstrip("=")
                payload = _b64.urlsafe_b64encode(
                    _json.dumps(
                        {
                            "sub": entry.subject,
                            "aud": entry.audience,
                            "iat": now_ts,
                            "exp": now_ts + ttl,
                            **entry.claims,
                        },
                        separators=(",", ":"),
                    ).encode()
                ).decode().rstrip("=")
                # Use HMAC fallback with a default key
                sig = hmac_sign(f"{header}.{payload}")
                token = f"{header}.{payload}.{sig}"
            else:
                token = create_jwt(
                    payload={
                        "sub": entry.subject,
                        "aud": entry.audience,
                        **entry.claims,
                    },
                    ttl=ttl,
                    audience=entry.audience,
                )

            # Decode parts for response
            parts = token.split(".")
            decoded = {}
            if len(parts) >= 2:
                try:
                    from app.utils import _pad_b64

                    payload_bytes = base64.urlsafe_b64decode(_pad_b64(parts[1]))
                    decoded = json.loads(payload_bytes.decode("utf-8"))
                except Exception:
                    decoded = {}

            tokens.append(
                {
                    "index": idx,
                    "subject": entry.subject,
                    "token": token,
                    "decoded": decoded,
                    "signature": parts[2] if len(parts) > 2 else "",
                }
            )
        except Exception as exc:
            logger.warning("batch_token_entry_failed", idx=idx, error=str(exc))
            tokens.append(
                {
                    "index": idx,
                    "subject": entry.subject,
                    "token": None,
                    "error": str(exc),
                }
            )

    logger.info("batch_tokens_generated", count=len(tokens))

    return BatchTokenResponse(
        tokens=tokens,
        request_id=request_id,
    )


# ── Batch Link Generation ───────────────────────────────────────────────────


@router.post(
    "/link/batch",
    response_model=BatchLinkResponse,
    summary="Batch generate signed links",
)
async def batch_generate_links(
    body: BatchLinkRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate multiple signed links in a single request.

    Each entry specifies a resource identifier and optional settings.
    Returns a JSON array of generated signed links.
    """
    if not body.entries:
        raise InvalidInputError("At least one entry is required")

    if len(body.entries) > 100:
        raise InvalidInputError("Maximum 100 entries per batch link request")

    import base64
    import json as json_mod
    from datetime import timedelta

    from app.crypto import ed25519_sign, generate_nonce, hmac_sign
    from app.utils import generate_id as gen_id, validate_ttl

    ttl = validate_ttl(body.ttl)
    expires_at = utcnow() + timedelta(seconds=ttl)
    links = []

    for idx, entry in enumerate(body.entries):
        try:
            if not entry.resource.strip():
                raise InvalidInputError("Resource identifier cannot be empty")

            nonce = generate_nonce()
            link_id = gen_id()

            token_payload = {
                "type": "signed-link",
                "resource": entry.resource,
                "id": link_id,
                "nonce": nonce,
                "iat": format_timestamp(utcnow()),
                "exp": format_timestamp(expires_at),
                "one_time": entry.one_time,
                "max_uses": entry.max_uses,
            }

            payload_bytes = json_mod.dumps(token_payload, separators=(",", ":")).encode("utf-8")

            try:
                signature_bytes = ed25519_sign(payload_bytes)
                sig_base64 = base64.b64encode(signature_bytes).decode("utf-8")
            except ValueError:
                sig_base64 = hmac_sign(payload_bytes.decode("utf-8"))

            payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
            token = f"{payload_b64}.{sig_base64}"
            url = f"https://claim.veilpass.app/c/{token}"

            links.append(
                {
                    "index": idx,
                    "resource": entry.resource,
                    "url": url,
                    "token": token,
                    "expires_at": format_timestamp(expires_at),
                    "signature": sig_base64,
                    "nonce": nonce,
                }
            )
        except Exception as exc:
            logger.warning("batch_link_entry_failed", idx=idx, error=str(exc))
            links.append(
                {
                    "index": idx,
                    "resource": entry.resource,
                    "url": None,
                    "error": str(exc),
                }
            )

    logger.info("batch_links_generated", count=len(links))

    return BatchLinkResponse(
        links=links,
        request_id=request_id,
    )


# ── Batch Dynamic QR Creation ───────────────────────────────────────────────


@router.post(
    "/dynamic-qr/batch",
    response_model=BatchDynamicQRResponse,
    summary="Batch create dynamic QR codes",
)
async def batch_create_dynamic_qr(
    body: BatchDynamicQRRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create multiple dynamic QR codes in bulk.

    Each entry specifies a destination URL and optional title/tags.
    Shared expiration and max_scans settings apply to all entries.
    """
    import re
    from uuid import uuid4

    if not body.entries:
        raise InvalidInputError("At least one entry is required")

    if len(body.entries) > 100:
        raise InvalidInputError("Maximum 100 entries per batch request")

    now = utcnow()
    expires_at = None
    if body.expires_in is not None and body.expires_in > 0:
        expires_at = now + timedelta(seconds=body.expires_in)

    url_pattern = re.compile(
        r"^https?://"
        r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"
        r"(:\d+)?"
        r"(/.*)?$"
    )

    items = []
    for idx, entry in enumerate(body.entries):
        try:
            if not entry.destination_url.strip():
                raise InvalidInputError("destination_url cannot be empty")

            if not url_pattern.match(entry.destination_url):
                raise InvalidInputError(
                    f"Invalid URL: {entry.destination_url}"
                )

            qr_id = f"qr_{generate_id()}"
            short_code = uuid4().hex[:12]

            store_entry = {
                "id": qr_id,
                "short_code": short_code,
                "destination_url": entry.destination_url,
                "title": entry.title,
                "allow_update": True,
                "max_scans": body.max_scans,
                "tags": entry.tags[:20],
                "created_at": now,
                "expires_at": expires_at,
                "updated_at": now,
                "active": True,
                "scan_count": 0,
            }
            _dynamic_qr_store[qr_id] = store_entry
            _dynamic_qr_store[short_code] = store_entry

            redirect_url = f"{_BASE_REDIRECT_DOMAIN}{short_code}"
            qr_image_url = f"/api/v1/dynamic-qr/{qr_id}/qr"

            items.append(
                DynamicQRResponse(
                    id=qr_id,
                    short_code=short_code,
                    redirect_url=redirect_url,
                    qr_image_url=qr_image_url,
                    created_at=format_timestamp(now),
                    expires_at=format_timestamp(expires_at) if expires_at else None,
                    request_id=request_id,
                )
            )
        except Exception as exc:
            logger.warning("batch_dynamic_qr_entry_failed", idx=idx, error=str(exc))
            items.append(
                DynamicQRResponse(
                    id="",
                    short_code="",
                    redirect_url="",
                    qr_image_url="",
                    created_at=format_timestamp(now),
                    request_id=request_id,
                )
            )

    logger.info("batch_dynamic_qr_created", count=len(items))

    return BatchDynamicQRResponse(
        items=[i for i in items if i.id],
        request_id=request_id,
    )


# ── Batch Status (placeholder for async batch jobs) ─────────────────────────


_batch_jobs: dict[str, dict] = {}


@router.get(
    "/batch/{batch_id}/status",
    response_model=BatchStatusResponse,
    summary="Check batch job status",
)
async def get_batch_status(
    batch_id: str,
    request_id: str = Depends(request_id_dependency),
):
    """Check the status of an asynchronous batch job.

    Currently returns synchronous completion for direct generation.
    In production this would track background job progress.
    """
    job = _batch_jobs.get(batch_id)
    if not job:
        raise InvalidInputError(f"Batch job not found: {batch_id}")

    return BatchStatusResponse(
        batch_id=batch_id,
        status=job.get("status", "completed"),
        total=job.get("total", 0),
        completed=job.get("completed", 0),
        failed=job.get("failed", 0),
        errors=job.get("errors", []),
        request_id=request_id,
    )
