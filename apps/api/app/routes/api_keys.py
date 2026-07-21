"""API key management endpoints for VeilPass API."""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.deps import api_key_dependency, rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError
from app.models.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyItem,
    ApiKeyListResponse,
    ApiKeyRevokeResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/api-keys", tags=["API Keys"])

# In-memory store for API keys (use DB in production)
_api_keys_store: dict[str, dict] = {}


@router.post("", response_model=ApiKeyCreateResponse, summary="Create an API key")
async def create_api_key(
    body: ApiKeyCreateRequest,
    _: None = Depends(rate_limit_dependency),
    __: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create a new API key with specified permissions."""
    if not body.name.strip():
        raise InvalidInputError("API key name cannot be empty")

    key_id = generate_id()
    raw_key = f"vp_{secrets.token_urlsafe(24)}"
    now = format_timestamp(utcnow())

    _api_keys_store[key_id] = {
        "id": key_id,
        "name": body.name,
        "prefix": raw_key[:12],
        "key_hash": hashlib.sha256(raw_key.encode()).hexdigest(),
        "created_at": now,
        "last_used_at": None,
        "permissions": body.permissions,
        "active": True,
    }

    logger.info("api_key_created", key_id=key_id, name=body.name)

    return ApiKeyCreateResponse(
        id=key_id,
        name=body.name,
        key=raw_key,
        created_at=now,
        permissions=body.permissions,
        request_id=request_id,
    )


@router.get("", response_model=ApiKeyListResponse, summary="List API keys")
async def list_api_keys(
    _: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """List all active API keys (shows prefix only)."""
    keys = []
    for key_id, data in _api_keys_store.items():
        if data.get("active", False):
            keys.append(
                ApiKeyItem(
                    id=key_id,
                    name=data["name"],
                    prefix=data["prefix"],
                    created_at=data["created_at"],
                    last_used_at=data.get("last_used_at"),
                    permissions=data.get("permissions", ["read"]),
                    active=True,
                )
            )

    return ApiKeyListResponse(keys=keys, request_id=request_id)


@router.delete("/{key_id}", response_model=ApiKeyRevokeResponse, summary="Revoke an API key")
async def revoke_api_key(
    key_id: str,
    _: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Revoke an API key by ID."""
    if key_id not in _api_keys_store:
        raise NotFoundError(f"API key not found: {key_id}")

    _api_keys_store[key_id]["active"] = False
    _api_keys_store[key_id]["revoked_at"] = format_timestamp(utcnow())

    logger.info("api_key_revoked", key_id=key_id)

    return ApiKeyRevokeResponse(
        message=f"API key {key_id} revoked",
        request_id=request_id,
    )
