"""Pydantic schemas for VeilPass API request/response models."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── QR Generation ──────────────────────────────────────────────────────────────


class QRGenerateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Data to encode in the QR code")
    format: str = Field(default="png", pattern=r"^(png|svg)$")
    ecl: str = Field(default="H", pattern=r"^[LMQH]$")
    size: int = Field(default=512, ge=64, le=4096)
    margin: int = Field(default=4, ge=0, le=20)
    color: str = Field(default="#000000", pattern=r"^#[0-9a-fA-F]{6}$")
    bg_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9a-fA-F]{6}$")
    include_logo: bool = False
    one_time: bool = False
    expires_in: Optional[int] = Field(default=None, ge=0)


class QRGenerateResponse(BaseModel):
    success: bool = True
    format: str
    encoding: str  # "raw" or "base64"
    data: str  # base64-encoded or raw bytes (returned via Response)
    content_type: str
    size: int
    expires_at: Optional[str] = None
    request_id: str = ""


# ── NFC Payload ────────────────────────────────────────────────────────────────


class NFCPayloadRequest(BaseModel):
    issuer: str = Field(default="veilpass", max_length=64)
    payload: str = Field(..., max_length=4096)
    version: str = Field(default="1.0", max_length=16)
    type: str = Field(default="uri", pattern=r"^(uri|text|phone|email|wifi|custom)$")
    expiration: Optional[str] = None  # ISO 8601
    metadata: dict[str, Any] = Field(default_factory=dict)


class NFCPayloadResponse(BaseModel):
    success: bool = True
    id: str
    type: str
    version: str
    issuer: str
    timestamp: str
    nonce: str
    signature: str
    payload: str
    exports: dict[str, str]  # json, hex, base64, ndef
    request_id: str = ""


# ── Signed Link ────────────────────────────────────────────────────────────────


class SignedLinkRequest(BaseModel):
    resource: str = Field(..., min_length=1, max_length=512)
    ttl: int = Field(default=86400, ge=0)
    one_time: bool = True
    max_uses: Optional[int] = Field(default=None, ge=1, le=100000)


class SignedLinkResponse(BaseModel):
    success: bool = True
    url: str
    token: str
    expires_at: str
    signature: str
    nonce: str
    request_id: str = ""


# ── Signed URL ─────────────────────────────────────────────────────────────────


class SignedURLRequest(BaseModel):
    url: str = Field(..., max_length=2048)
    permissions: str = Field(default="read", pattern=r"^(read|write|read,write)$")
    expires_in: int = Field(default=3600, ge=0)
    download_limit: Optional[int] = Field(default=None, ge=1, le=10000)
    one_time: bool = False


class SignedURLResponse(BaseModel):
    success: bool = True
    signed_url: str
    expires: str
    signature: str
    key_id: str
    request_id: str = ""


# ── Token ──────────────────────────────────────────────────────────────────────


class TokenRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=256)
    audience: str = Field(default="api.veilpass.app", max_length=256)
    issuer: str = Field(default="veilpass", max_length=64)
    expires_in: int = Field(default=86400, ge=0)
    claims: dict[str, Any] = Field(default_factory=dict)


class TokenResponse(BaseModel):
    success: bool = True
    token: str
    decoded: dict[str, Any]
    signature: str
    expires_at: str
    request_id: str = ""


# ── Verification ────────────────────────────────────────────────────────────────


class VerifyRequest(BaseModel):
    type: str = Field(..., pattern=r"^(token|signed-link|signed-url)$")
    value: str = Field(..., max_length=8192)


class VerifyResponse(BaseModel):
    success: bool = True
    valid: bool
    expired: bool
    issuer: str
    signature_valid: bool
    claims: dict[str, Any]
    request_id: str = ""


# ── API Keys ───────────────────────────────────────────────────────────────────


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    permissions: list[str] = Field(default_factory=lambda: ["read"])


class ApiKeyCreateResponse(BaseModel):
    success: bool = True
    id: str
    name: str
    key: str  # the full API key (only shown on creation)
    created_at: str
    permissions: list[str]
    request_id: str = ""


class ApiKeyItem(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: str
    last_used_at: Optional[str] = None
    permissions: list[str]
    active: bool


class ApiKeyListResponse(BaseModel):
    success: bool = True
    keys: list[ApiKeyItem]
    request_id: str = ""


class ApiKeyRevokeResponse(BaseModel):
    success: bool = True
    message: str
    request_id: str = ""


# ── Health ─────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# ── Error ──────────────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str = ""


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
