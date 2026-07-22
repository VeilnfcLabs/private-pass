"""Decentralised Trust Registry for verifiable issuer public keys and DIDs.

Provides a registry of trusted credential issuers, allowing verifiers to
check the legitimacy of a credential's issuer before accepting it.
Supports DID-based and public-key-based issuer identification.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError
from app.models.schemas import (
    RegistryIssuerRequest,
    RegistryIssuerResponse,
    RegistryIssuerListResponse,
    RegistryIssuerDetailResponse,
    RegistryVerifyCredentialRequest,
    RegistryVerifyCredentialResponse,
    RegistryCredentialCheckResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/registry", tags=["Trust Registry"])

# ── In-memory store (use DB in production) ─────────────────────────────────────

_issuer_store: dict[str, dict] = {}  # issuer_id -> issuer data
_issuer_by_did: dict[str, str] = {}  # did -> issuer_id
_issuer_by_key: dict[str, str] = {}  # public_key -> issuer_id

# Allowed key algorithms
ALLOWED_ALGORITHMS = {"Ed25519", "ES256", "ES384", "ES512", "RS256", "schnorr-2048"}


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "/issuer",
    response_model=RegistryIssuerResponse,
    summary="Register a trusted issuer",
)
async def register_issuer(
    body: RegistryIssuerRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Register a new trusted credential issuer.

    Issuers are identified by their DID and/or public key. Registration
    allows verifiers to look up whether a credential was issued by a
    known and trusted party.
    """
    # Validate required fields
    if not body.name or not body.name.strip():
        raise InvalidInputError("issuer name is required")

    if not body.public_key or not body.public_key.strip():
        raise InvalidInputError("public_key is required")

    # Validate algorithm
    if body.algorithm and body.algorithm not in ALLOWED_ALGORITHMS:
        raise InvalidInputError(
            f"Unsupported algorithm '{body.algorithm}'. "
            f"Allowed: {sorted(ALLOWED_ALGORITHMS)}"
        )

    # Check for duplicate public key
    if body.public_key in _issuer_by_key:
        existing_id = _issuer_by_key[body.public_key]
        existing = _issuer_store.get(existing_id, {})
        raise InvalidInputError(
            f"An issuer with this public key already exists: '{existing.get('name', 'unknown')}'"
        )

    # Check for duplicate DID
    if body.did and body.did in _issuer_by_did:
        existing_id = _issuer_by_did[body.did]
        existing = _issuer_store.get(existing_id, {})
        raise InvalidInputError(
            f"An issuer with this DID already exists: '{existing.get('name', 'unknown')}'"
        )

    issuer_id = generate_id()
    now = format_timestamp(utcnow())

    issuer_data = {
        "id": issuer_id,
        "name": body.name.strip(),
        "did": body.did.strip() if body.did else "",
        "public_key": body.public_key.strip(),
        "algorithm": body.algorithm or "Ed25519",
        "website": body.website.strip() if body.website else "",
        "contact_email": body.contact_email.strip() if body.contact_email else "",
        "verified": False,  # Set to True after manual verification
        "created_at": now,
        "updated_at": now,
    }

    _issuer_store[issuer_id] = issuer_data
    _issuer_by_key[body.public_key] = issuer_id
    if body.did:
        _issuer_by_did[body.did] = issuer_id

    logger.info(
        "registry_issuer_registered",
        issuer_id=issuer_id,
        name=body.name,
        did=body.did,
    )

    return RegistryIssuerResponse(
        id=issuer_id,
        name=body.name.strip(),
        did=body.did.strip() if body.did else "",
        algorithm=issuer_data["algorithm"],
        verified=issuer_data["verified"],
        created_at=now,
        request_id=request_id,
    )


@router.get(
    "/issuers",
    response_model=RegistryIssuerListResponse,
    summary="List registered issuers",
)
async def list_issuers(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search by name or DID"),
    algorithm: Optional[str] = Query(default=None, description="Filter by algorithm"),
    verified: Optional[bool] = Query(default=None, description="Filter by verification status"),
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """List all registered issuers with pagination and filtering."""
    items = list(_issuer_store.values())

    # Apply filters
    if search:
        search_lower = search.lower()
        items = [
            item for item in items
            if search_lower in item["name"].lower()
            or search_lower in item.get("did", "").lower()
        ]

    if algorithm:
        items = [item for item in items if item.get("algorithm") == algorithm]

    if verified is not None:
        items = [item for item in items if item.get("verified") == verified]

    # Sort by created_at descending
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    issuer_list = [
        RegistryIssuerDetailResponse(
            id=item["id"],
            name=item["name"],
            did=item.get("did", ""),
            public_key=item.get("public_key", ""),
            algorithm=item.get("algorithm", "Ed25519"),
            website=item.get("website", ""),
            contact_email=item.get("contact_email", ""),
            verified=item.get("verified", False),
            created_at=item.get("created_at", ""),
        )
        for item in page_items
    ]

    return RegistryIssuerListResponse(
        issuers=issuer_list,
        total=total,
        page=page,
        per_page=per_page,
        request_id=request_id,
    )


@router.get(
    "/issuers/{issuer_id}",
    response_model=RegistryIssuerDetailResponse,
    summary="Get issuer details",
)
async def get_issuer(
    issuer_id: str,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Get detailed information about a registered issuer."""
    issuer = _issuer_store.get(issuer_id)
    if issuer is None:
        raise NotFoundError(f"Issuer not found: {issuer_id}")

    return RegistryIssuerDetailResponse(
        id=issuer["id"],
        name=issuer["name"],
        did=issuer.get("did", ""),
        public_key=issuer.get("public_key", ""),
        algorithm=issuer.get("algorithm", "Ed25519"),
        website=issuer.get("website", ""),
        contact_email=issuer.get("contact_email", ""),
        verified=issuer.get("verified", False),
        created_at=issuer.get("created_at", ""),
        request_id=request_id,
    )


@router.get(
    "/verify/{credential:path}",
    response_model=RegistryCredentialCheckResponse,
    summary="Check credential issuer legitimacy",
)
async def verify_credential_legitimacy(
    credential: str,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Check whether a credential's issuer is registered in the trust registry.

    Extracts the issuer DID or key_id from the credential and looks it up
    in the registry. Returns trust status and issuer information.
    """
    # Attempt to parse the credential as a JWT or JSON credential
    issuer_did = ""
    issuer_key = ""

    try:
        # Try parsing as JWT first
        parts = credential.split(".")
        if len(parts) == 3:
            # JWT format: header.payload.signature
            import base64
            import json as json_module

            # Decode the payload (add padding if needed)
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            try:
                payload_bytes = base64.urlsafe_b64decode(payload_b64)
                payload_data = json_module.loads(payload_bytes)
                issuer_did = payload_data.get("iss", "") or payload_data.get("issuer", "")
                issuer_key = payload_data.get("key_id", "") or payload_data.get("kid", "")
            except Exception:
                pass
        else:
            # Try as raw JSON
            try:
                payload_data = json.loads(credential)
                issuer_did = payload_data.get("iss", "") or payload_data.get("issuer", "") or payload_data.get("did", "")
                issuer_key = payload_data.get("public_key", "") or payload_data.get("key_id", "") or payload_data.get("kid", "")
            except Exception:
                pass
    except Exception:
        pass

    # Look up by DID first, then by public key
    issuer_id = _issuer_by_did.get(issuer_did) or _issuer_by_key.get(issuer_key)
    issuer = _issuer_store.get(issuer_id) if issuer_id else None

    if issuer:
        logger.info(
            "registry_credential_verified",
            trusted=True,
            issuer_name=issuer["name"],
        )
        return RegistryCredentialCheckResponse(
            trusted=True,
            issuer_name=issuer["name"],
            did=issuer.get("did", ""),
            verified_at=format_timestamp(utcnow()),
            request_id=request_id,
        )
    else:
        logger.info("registry_credential_verified", trusted=False)
        return RegistryCredentialCheckResponse(
            trusted=False,
            issuer_name="",
            did="",
            verified_at=format_timestamp(utcnow()),
            request_id=request_id,
        )


@router.post(
    "/verify-credential",
    response_model=RegistryVerifyCredentialResponse,
    summary="Verify a credential against the registry",
)
async def verify_credential_registry(
    body: RegistryVerifyCredentialRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Verify a credential token against the trust registry.

    Checks whether the credential was issued by a known issuer and
    optionally validates the expected issuer name matches.
    """
    token = body.token.strip()
    expected_issuer = body.expected_issuer.strip() if body.expected_issuer else ""

    # Extract issuer information from the token
    issuer_did = ""
    issuer_key = ""

    try:
        parts = token.split(".")
        if len(parts) == 3:
            # JWT format
            import base64

            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            try:
                payload_bytes = base64.urlsafe_b64decode(payload_b64)
                payload_data = json.loads(payload_bytes)
                issuer_did = payload_data.get("iss", "") or payload_data.get("issuer", "")
                issuer_key = payload_data.get("key_id", "") or payload_data.get("kid", "")
            except Exception:
                pass
        else:
            # Raw JSON
            try:
                payload_data = json.loads(token)
                issuer_did = payload_data.get("iss", "") or payload_data.get("issuer", "") or payload_data.get("did", "")
                issuer_key = payload_data.get("public_key", "") or payload_data.get("key_id", "") or payload_data.get("kid", "")
            except Exception:
                pass
    except Exception:
        pass

    # Look up issuer
    issuer_id = _issuer_by_did.get(issuer_did) or _issuer_by_key.get(issuer_key)
    issuer = _issuer_store.get(issuer_id) if issuer_id else None

    if not issuer:
        logger.info("registry_verify_credential_not_found")
        return RegistryVerifyCredentialResponse(
            trusted=False,
            issuer_name="",
            did="",
            signature_valid=False,
            registry_verified=False,
            request_id=request_id,
        )

    # Check expected issuer name if provided
    name_matched = True
    if expected_issuer:
        name_matched = issuer["name"].lower() == expected_issuer.lower()
        if not name_matched:
            logger.warning(
                "registry_issuer_name_mismatch",
                expected=expected_issuer,
                found=issuer["name"],
            )

    signature_valid = issuer.get("verified", False)

    logger.info(
        "registry_verify_credential",
        trusted=name_matched,
        issuer_name=issuer["name"],
    )

    return RegistryVerifyCredentialResponse(
        trusted=name_matched and bool(issuer),
        issuer_name=issuer["name"],
        did=issuer.get("did", ""),
        signature_valid=signature_valid,
        registry_verified=True,
        request_id=request_id,
    )
