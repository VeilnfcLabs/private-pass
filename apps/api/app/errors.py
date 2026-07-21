"""Structured error handling for VeilPass API."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from structlog import get_logger

logger = get_logger(__name__)


class VeilPassError(Exception):
    """Base error for all VeilPass API errors."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self, request_id: str = "") -> dict[str, Any]:
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "request_id": request_id,
            },
        }


# ── Specific error shortcuts ──────────────────────────────────────────────────


class TokenExpiredError(VeilPassError):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(code="TOKEN_EXPIRED", message=message, status_code=401)


class InvalidSignatureError(VeilPassError):
    def __init__(self, message: str = "Invalid signature"):
        super().__init__(code="INVALID_SIGNATURE", message=message, status_code=401)


class InvalidTokenError(VeilPassError):
    def __init__(self, message: str = "Invalid token"):
        super().__init__(code="INVALID_TOKEN", message=message, status_code=401)


class RateLimitedError(VeilPassError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(code="RATE_LIMITED", message=message, status_code=429)


class InvalidInputError(VeilPassError):
    def __init__(self, message: str = "Invalid input"):
        super().__init__(code="INVALID_INPUT", message=message, status_code=400)


class NotFoundError(VeilPassError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="NOT_FOUND", message=message, status_code=404)


class InternalError(VeilPassError):
    def __init__(self, message: str = "Internal server error"):
        super().__init__(code="INTERNAL_ERROR", message=message, status_code=500)


# ── Global exception handler ───────────────────────────────────────────────────


async def veilpass_exception_handler(request: Request, exc: VeilPassError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    logger.error(
        "veilpass_error",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        path=str(request.url),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(request_id=request_id),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions — never expose internals."""
    request_id = getattr(request.state, "request_id", "")
    logger.exception(
        "unhandled_exception",
        request_id=request_id,
        path=str(request.url),
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id,
            },
        },
    )
