"""Pydantic schemas for VeilPass API request/response models."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

# ── Selective Disclosure JWT (SD-JWT) ────────────────────────────────


class SDJWTRequest(BaseModel):
    subject: str = Field(..., max_length=256)
    audience: str = Field(default="api.veilpass.app", max_length=256)
    issuer: str = Field(default="veilpass", max_length=64)
    expires_in: int = Field(default=86400, ge=0)
    claims: dict[str, Any]
    disclosable_claims: Optional[list[str]] = Field(
        default=None,
        description="Claims eligible for selective disclosure. "
        "None = all claims are disclosable, empty list = none are disclosable.",
    )


class SDJWTResponse(BaseModel):
    success: bool = True
    token: str
    disclosures: list[str]
    disclosable_claims: list[str]
    expires_at: str
    request_id: str = ""


class SDJWTPresentRequest(BaseModel):
    token: str
    disclosures: list[str]
    reveal_claims: list[str]


class SDJWTPresentResponse(BaseModel):
    success: bool = True
    presentation_token: str
    disclosures: list[str]
    disclosed_claims: list[str]
    request_id: str = ""


class SDJWTVeirfyResponse(BaseModel):
    """Response for SD-JWT verification (name kept for API compatibility)."""

    success: bool = True
    valid: bool
    expired: bool
    disclosed_claims: dict[str, Any]
    request_id: str = ""


# ── Revocation ────────────────────────────────────────────────────────


class RevokeRequest(BaseModel):
    id: str = Field(..., max_length=256)
    reason: str = Field(default="no_reason", max_length=512)


class RevokeResponse(BaseModel):
    success: bool = True
    id: str
    status: str
    revoked_at: str
    request_id: str = ""


class StatusResponse(BaseModel):
    success: bool = True
    id: str
    status: str  # "valid" | "revoked" | "expired"
    status_purpose: str = "revocation"
    revoked_at: Optional[str] = None
    reason: Optional[str] = None
    request_id: str = ""


class BulkRevokeRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1, max_length=1000)
    reason: str = Field(default="no_reason", max_length=512)


class BulkRevokeItem(BaseModel):
    id: str
    status: str
    revoked_at: str


class BulkRevokeResponse(BaseModel):
    success: bool = True
    results: list[BulkRevokeItem]
    total: int
    request_id: str = ""


class RevokeListItem(BaseModel):
    id: str
    status: str
    reason: str = ""
    revoked_at: str


class RevokeListResponse(BaseModel):
    success: bool = True
    revoked: list[RevokeListItem]
    total: int
    page: int = 1
    request_id: str = ""


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
    bind_to_uid: bool = Field(default=False, description="Bind payload to a specific NFC tag UID (anti-cloning)")
    uid: Optional[str] = Field(default=None, max_length=64, description="NFC tag UID (e.g. 04:12:34:56:78:9A:BC)")


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


# ── Webhooks ───────────────────────────────────────────────────────────────────


class WebhookRequest(BaseModel):
    url: str = Field(..., max_length=2048)
    events: list[str] = Field(..., min_length=1)
    secret: str = Field(default="", max_length=256)
    description: Optional[str] = Field(default=None, max_length=512)


class WebhookResponse(BaseModel):
    success: bool = True
    id: str
    url: str
    events: list[str]
    active: bool
    created_at: str
    updated_at: str
    request_id: str = ""


class WebhookListResponse(BaseModel):
    success: bool = True
    webhooks: list[WebhookResponse]
    total: int
    request_id: str = ""


class WebhookEventResponse(BaseModel):
    success: bool = True
    id: str
    webhook_id: str
    event_type: str
    status: str
    created_at: str
    request_id: str = ""


# ── Signing Keys ───────────────────────────────────────────────────────────────


class SigningKeyResponse(BaseModel):
    success: bool = True
    id: str
    key_id: str
    purpose: str
    algorithm: str
    public_key: str
    created_at: str
    active: bool
    expires_at: Optional[str] = None
    tags: list[str] = []
    request_id: str = ""


class SigningKeyListResponse(BaseModel):
    success: bool = True
    keys: list[SigningKeyResponse]
    total: int
    active_key_id: Optional[str] = None
    request_id: str = ""


class RotateKeysRequest(BaseModel):
    reason: str = Field(default="scheduled", max_length=256)


class RotateKeysResponse(BaseModel):
    success: bool = True
    new_key_id: str
    previous_key_id: str
    rotated_at: str
    request_id: str = ""


# ── Audit Log ──────────────────────────────────────────────────────────────────


class AuditLogResponse(BaseModel):
    success: bool = True
    id: str
    event_type: str
    actor: str
    resource_id: str
    action: str
    details: dict[str, Any]
    ip_address: str
    timestamp: str
    request_id: str = ""


class AuditLogListResponse(BaseModel):
    success: bool = True
    entries: list[AuditLogResponse]
    total: int
    page: int
    request_id: str = ""


# ── Hybrid NFC + QR Encrypted Payloads ─────────────────────────────────────


class EncryptedPayloadRequest(BaseModel):
    payload: str = Field(..., min_length=1, max_length=65536, description="Sensitive data to encrypt")
    password: str = Field(..., min_length=4, max_length=512, description="User-chosen encryption password")
    output_format: str = Field(default="both", pattern=r"^(both|nfc|qr)$")
    nfc_type: str = Field(default="uri", pattern=r"^(uri|text|phone|email|wifi|custom)$")
    qr_format: str = Field(default="png", pattern=r"^(png|svg)$")


class EncryptedData(BaseModel):
    ciphertext: str = Field(..., description="Base64-encoded ciphertext")
    nonce: str = Field(..., description="Base64-encoded nonce")
    tag: str = Field(..., description="Base64-encoded GCM authentication tag")
    algorithm: str = "AES-256-GCM"
    kdf: str = "SHA-256"


class NFCPayloadContainer(BaseModel):
    hex: str = ""
    base64: str = ""
    ndef: str = ""


class EncryptedPayloadResponse(BaseModel):
    success: bool = True
    id: str
    encrypted: EncryptedData
    nfc_payload: Optional[NFCPayloadContainer] = None
    qr_data: Optional[str] = Field(default=None, description="Base64-encoded QR image")
    decryption_key_hint: str = "SHA-256(password)"
    created_at: str
    request_id: str = ""


class DecryptPayloadRequest(BaseModel):
    encrypted: EncryptedData
    password: str = Field(..., min_length=4, max_length=512)


class DecryptPayloadResponse(BaseModel):
    success: bool = True
    plaintext: str
    algorithm: str = "AES-256-GCM"
    request_id: str = ""


class NFCFromEncryptedRequest(BaseModel):
    encrypted: EncryptedData
    nfc_type: str = Field(default="uri", pattern=r"^(uri|text|phone|email|wifi|custom)$")


class NFCFromEncryptedResponse(BaseModel):
    success: bool = True
    nfc_payload: NFCPayloadContainer
    request_id: str = ""


class QRFromEncryptedRequest(BaseModel):
    encrypted: EncryptedData
    qr_format: str = Field(default="png", pattern=r"^(png|svg)$")


class QRFromEncryptedResponse(BaseModel):
    success: bool = True
    qr_data: str
    request_id: str = ""


# ── Post-Quantum Cryptography (PQ) ─────────────────────────────────────────


class PQAlgorithmItem(BaseModel):
    id: str
    name: str
    nist_level: int
    signature_size: str
    public_key_size: str
    status: str
    available: bool


class PQAlgorithmListResponse(BaseModel):
    success: bool = True
    algorithms: list[PQAlgorithmItem]
    request_id: str = ""


class PQSignRequest(BaseModel):
    payload: str = Field(..., min_length=1, max_length=65536)
    algorithm: str = Field(..., pattern=r"^(ML-DSA-65|ML-DSA-87|FN-DSA-512|SLH-DSA-128s)$")
    private_key: str = Field(..., description="Base64-encoded private key")


class PQSignResponse(BaseModel):
    success: bool = True
    signature: str
    algorithm: str
    public_key: str
    request_id: str = ""


class PQVerifyRequest(BaseModel):
    payload: str = Field(..., min_length=1, max_length=65536)
    signature: str = Field(..., description="Base64-encoded signature")
    algorithm: str = Field(..., pattern=r"^(ML-DSA-65|ML-DSA-87|FN-DSA-512|SLH-DSA-128s)$")
    public_key: str = Field(..., description="Base64-encoded public key")


class PQVerifyResponse(BaseModel):
    success: bool = True
    valid: bool
    algorithm: str
    request_id: str = ""


# ── NFC Anti-Cloning (UID Binding) ─────────────────────────────────────────


class NFCUidVerifyRequest(BaseModel):
    payload: dict[str, Any] = Field(..., description="The NFC payload document to verify")
    uid: str = Field(..., max_length=64, description="NFC tag UID to verify against")


class NFCUidVerifyResponse(BaseModel):
    success: bool = True
    uid_match: bool
    signature_valid: bool
    uid_in_payload: bool
    request_id: str = ""


class NFCExportWithUid(BaseModel):
    """NFC export format that includes UID binding information."""
    payload_json: str = Field(default="", alias="json")
    hex: str = ""
    base64: str = ""
    ndef: str = ""
    uid: Optional[str] = None
    uid_locked: bool = False
    uid_included_in_signature: bool = False
    signature_hex: str = ""
    signature_base64: str = ""

    model_config = {"populate_by_name": True}


# ── Privacy-First Analytics ────────────────────────────────────────────────


class PrivacyScoreResponse(BaseModel):
    success: bool = True
    score: int = Field(..., ge=0, le=100)
    compliant_with: list[str]
    data_retention_days: int
    auto_delete: bool
    request_id: str = ""


# ── Dynamic QR ──────────────────────────────────────────────────────────────


class DynamicQRRequest(BaseModel):
    destination_url: str = Field(..., max_length=2048)
    title: Optional[str] = Field(default=None, max_length=256)
    allow_update: bool = True
    expires_in: Optional[int] = Field(default=2592000, ge=0)
    max_scans: Optional[int] = Field(default=None, ge=1, le=1000000)
    tags: list[str] = Field(default_factory=list)
    privacy_mode: str = Field(default="standard", pattern=r"^(standard|privacy|aggregate_only)$",
                              description="Privacy mode for analytics: standard (full), privacy (anonymized), aggregate_only (count only)")


class DynamicQRResponse(BaseModel):
    success: bool = True
    id: str
    short_code: str
    redirect_url: str
    qr_image_url: str
    created_at: str
    expires_at: Optional[str] = None
    request_id: str = ""


class DynamicQRUpdateRequest(BaseModel):
    destination_url: str = Field(..., max_length=2048)


class QRAnalyticsResponse(BaseModel):
    success: bool = True
    id: str
    total_scans: int
    unique_ips: int
    scans_over_time: list[dict]
    top_user_agents: list[dict]
    top_referrers: list[dict]
    last_scan: Optional[str] = None
    request_id: str = ""


class DynamicQRListItem(BaseModel):
    id: str
    short_code: str
    title: Optional[str]
    destination_url: str
    total_scans: int
    created_at: str
    expires_at: Optional[str]
    active: bool
    tags: list[str]


class DynamicQRListResponse(BaseModel):
    success: bool = True
    items: list[DynamicQRListItem]
    total: int
    page: int
    per_page: int
    request_id: str = ""


# ── Batch ───────────────────────────────────────────────────────────────────


class BatchEntry(BaseModel):
    content: str
    filename: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchQRRequest(BaseModel):
    entries: list[BatchEntry]
    format: str = Field(default="png", pattern=r"^(png|svg)$")
    ecl: str = Field(default="H", pattern=r"^[LMQH]$")
    size: int = Field(default=512, ge=64, le=4096)


class BatchQRResponse(BaseModel):
    success: bool = True
    count: int
    download_url: str = ""
    request_id: str = ""


class BatchTokenEntry(BaseModel):
    subject: str = Field(..., min_length=1, max_length=256)
    audience: str = "api.veilpass.app"
    claims: dict[str, Any] = Field(default_factory=dict)


class BatchTokenRequest(BaseModel):
    entries: list[BatchTokenEntry]
    ttl: int = Field(default=86400, ge=0)


class BatchTokenResponse(BaseModel):
    success: bool = True
    tokens: list[dict]
    request_id: str = ""


class BatchLinkEntry(BaseModel):
    resource: str = Field(..., min_length=1, max_length=512)
    one_time: bool = True
    max_uses: Optional[int] = Field(default=None, ge=1, le=100000)


class BatchLinkRequest(BaseModel):
    entries: list[BatchLinkEntry]
    ttl: int = Field(default=86400, ge=0)


class BatchLinkResponse(BaseModel):
    success: bool = True
    links: list[dict]
    request_id: str = ""


class BatchDynamicQREntry(BaseModel):
    destination_url: str = Field(..., max_length=2048)
    title: Optional[str] = Field(default=None, max_length=256)
    tags: list[str] = Field(default_factory=list)


class BatchDynamicQRRequest(BaseModel):
    entries: list[BatchDynamicQREntry]
    expires_in: Optional[int] = Field(default=2592000, ge=0)
    max_scans: Optional[int] = Field(default=None, ge=1, le=1000000)


class BatchDynamicQRResponse(BaseModel):
    success: bool = True
    items: list[DynamicQRResponse]
    request_id: str = ""


class BatchStatusResponse(BaseModel):
    success: bool = True
    batch_id: str
    status: str
    total: int
    completed: int
    failed: int
    errors: list[str]


# ── Templates ───────────────────────────────────────────────────────────────


class TemplateRequest(BaseModel):
    name: str = Field(..., max_length=256)
    description: Optional[str] = Field(default=None, max_length=1024)
    type: str = Field(..., pattern=r"^(signed-link|signed-url|token|qr|nfc)$")
    config: dict[str, Any]
    tags: list[str] = Field(default_factory=list)


class TemplateResponse(BaseModel):
    success: bool = True
    id: str
    name: str
    description: Optional[str]
    type: str
    config: dict[str, Any]
    version: int
    tags: list[str]
    created_at: str
    updated_at: str
    request_id: str = ""


class TemplateListResponse(BaseModel):
    success: bool = True
    templates: list[TemplateResponse]
    total: int
    page: int
    per_page: int
    request_id: str = ""


class TemplateRenderRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)


class TemplateRenderResponse(BaseModel):
    success: bool = True
    id: str
    type: str
    rendered: dict[str, Any]
    request_id: str = ""


class TemplatePreviewResponse(BaseModel):
    success: bool = True
    id: str
    name: str
    type: str
    preview: dict[str, Any]
    request_id: str = ""


# ── Zero-Knowledge Proof (ZKP) ──────────────────────────────────────────────


class ZKPKeypairResponse(BaseModel):
    success: bool = True
    key_id: str
    private_key: str
    public_key: str
    algorithm: str = "schnorr-2048"
    created_at: str
    request_id: str = ""


class ZKPProofRequest(BaseModel):
    private_key: str = Field(..., description="The private key (integer as string)")


class ZKPProofData(BaseModel):
    t: str
    s: str
    nonce: str
    timestamp: str


class ZKPProofResponse(BaseModel):
    success: bool = True
    proof: ZKPProofData
    qr_data: str
    request_id: str = ""


class ZKPVerifyRequest(BaseModel):
    proof: ZKPProofData
    public_key: str = Field(..., description="The public key (integer as string)")


class ZKPVerifyResponse(BaseModel):
    success: bool = True
    valid: bool
    verified_at: str
    proof_fresh: bool
    request_id: str = ""


class ZKPRegisterKeyRequest(BaseModel):
    public_key: str = Field(..., description="Public key to register")
    label: str = Field(default="Unnamed", max_length=256, description="Human-readable label")


class ZKPRegisterKeyResponse(BaseModel):
    success: bool = True
    public_key: str
    label: str
    registered_at: str
    request_id: str = ""


class ZKPRegisteredKeyItem(BaseModel):
    public_key: str
    label: str
    registered_at: str


class ZKPRegisteredKeysResponse(BaseModel):
    success: bool = True
    keys: list[ZKPRegisteredKeyItem]
    total: int
    request_id: str = ""


# ── Ephemeral Credentials ───────────────────────────────────────────────────


class EphemeralTokenRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=256, description="Subject identifier")
    ttl: int = Field(default=300, ge=0, description="Time-to-live in seconds (300, 600, 1800, 3600, or 86400)")
    one_time: bool = Field(default=True, description="Auto-self-destruct after first use")
    purpose: str = Field(default="", max_length=256, description="Purpose of the ephemeral credential")


class EphemeralTokenResponse(BaseModel):
    success: bool = True
    token: str
    expires_in: int
    one_time: bool
    expires_at: str
    request_id: str = ""


class EphemeralVerifyRequest(BaseModel):
    token: str = Field(..., description="Ephemeral token to verify")


class EphemeralVerifyResponse(BaseModel):
    success: bool = True
    valid: bool
    subject: str
    purpose: str
    expired: bool
    one_time_used: bool
    request_id: str = ""


class EphemeralRevokeRequest(BaseModel):
    token: str = Field(..., description="Ephemeral token to revoke")
    reason: str = Field(default="manual_revocation", max_length=512)


class EphemeralRevokeResponse(BaseModel):
    success: bool = True
    token: str
    revoked: bool
    revoked_at: str
    request_id: str = ""


# ── Trust Registry ──────────────────────────────────────────────────────────


class RegistryIssuerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256, description="Issuer name")
    did: str = Field(default="", max_length=512, description="Decentralized Identifier (DID)")
    public_key: str = Field(..., min_length=1, max_length=2048, description="Issuer public key")
    algorithm: str = Field(default="Ed25519", max_length=64, description="Key algorithm")
    website: str = Field(default="", max_length=2048, description="Issuer website URL")
    contact_email: str = Field(default="", max_length=256, description="Issuer contact email")


class RegistryIssuerResponse(BaseModel):
    success: bool = True
    id: str
    name: str
    did: str
    algorithm: str
    verified: bool
    created_at: str
    request_id: str = ""


class RegistryIssuerDetailResponse(BaseModel):
    success: bool = True
    id: str
    name: str
    did: str
    public_key: str
    algorithm: str
    website: str
    contact_email: str
    verified: bool
    created_at: str
    request_id: str = ""


class RegistryIssuerListResponse(BaseModel):
    success: bool = True
    issuers: list[RegistryIssuerDetailResponse]
    total: int
    page: int
    per_page: int
    request_id: str = ""


class RegistryCredentialCheckResponse(BaseModel):
    success: bool = True
    trusted: bool
    issuer_name: str
    did: str
    verified_at: str
    request_id: str = ""


class RegistryVerifyCredentialRequest(BaseModel):
    token: str = Field(..., max_length=16384, description="Credential token to verify")
    expected_issuer: str = Field(default="", max_length=256, description="Expected issuer name")


class RegistryVerifyCredentialResponse(BaseModel):
    success: bool = True
    trusted: bool
    issuer_name: str
    did: str
    signature_valid: bool
    registry_verified: bool
    request_id: str = ""
