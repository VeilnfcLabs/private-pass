"""QR code generation endpoint for VeilPass API."""

import io
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional

import qrcode
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import QRGenerateRequest
from app.utils import truncate_content, validate_ttl, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/qr", tags=["QR"])

# ECL mapping
_ECL_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


@router.post("", summary="Generate a QR code")
async def generate_qr(
    body: QRGenerateRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate a QR code image in PNG or SVG format."""
    content = truncate_content(body.content)

    if not content.strip():
        raise InvalidInputError("QR content cannot be empty")

    ecl = _ECL_MAP.get(body.ecl, qrcode.constants.ERROR_CORRECT_H)
    qr = qrcode.QRCode(
        version=None,
        error_correction=ecl,
        box_size=body.size // 100 if body.size > 100 else 10,
        border=body.margin,
    )
    qr.add_data(content)
    try:
        qr.make(fit=True)
    except ValueError as e:
        raise InvalidInputError(
            f"QR content too large for the selected parameters: {e}"
        )

    expires_at: Optional[str] = None
    if body.expires_in is not None:
        ttl = validate_ttl(body.expires_in)
        if ttl > 0:
            expires_at = format_timestamp(utcnow() + timedelta(seconds=ttl))

    if body.format == "svg":
        from qrcode.image.svg import SvgPathImage

        img = qr.make_image(image_factory=SvgPathImage, fill_color=body.color, back_color=body.bg_color)
        buffer = io.BytesIO()
        img.save(buffer)
        svg_bytes = buffer.getvalue()

        if body.include_logo:
            logger.warning("logo_embedding_not_supported_for_svg")

        return Response(
            content=svg_bytes,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": "inline; filename=veilpass-qr.svg",
                "X-Request-ID": request_id,
            },
        )

    # PNG generation
    img = qr.make_image(
        fill_color=body.color,
        back_color=body.bg_color,
    )

    if body.include_logo:
        logger.info("logo_requested_but_embedding_requires_pil_composite")

    # Resize if needed
    if body.size != img.size[0]:
        img = img.resize((body.size, body.size))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    # If client wants base64 (check Accept header or query param)
    accept = request.headers.get("Accept", "")
    if "application/json" in accept or body.format == "png_base64":
        encoded = base64.b64encode(png_bytes).decode("utf-8")
        return {
            "success": True,
            "format": "png",
            "encoding": "base64",
            "data": encoded,
            "content_type": "image/png",
            "size": body.size,
            "expires_at": expires_at,
            "request_id": request_id,
        }

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": "inline; filename=veilpass-qr.png",
            "X-Request-ID": request_id,
        },
    )
