"""Revocation support for VeilPass tokens and credentials.

Provides endpoints to revoke tokens/credentials, check status,
list revoked items, bulk revoke, and a W3C StatusList2021-compatible
status check.
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from structlog import get_logger

from app.deps import api_key_dependency, rate_limit_dependency, request_id_dependency
from app.models.schemas import (
    BulkRevokeItem,
    BulkRevokeRequest,
    BulkRevokeResponse,
    RevokeListItem,
    RevokeListResponse,
    RevokeRequest,
    RevokeResponse,
    StatusResponse,
)
from app.utils import format_timestamp, utcnow

logger = get_logger(__name__)

# ── Routers ───────────────────────────────────────────────────────────
# Two routers: one for /api/v1/revoke/* and one for /api/v1/status/*
# (W3C StatusList2021 compatible endpoint).

revoke_router = APIRouter(prefix="/api/v1/revoke", tags=["Revocation"])
status_router = APIRouter(prefix="/api/v1/status", tags=["Status"])

# ── In-memory revocation store ────────────────────────────────────────
# Use Redis or a database in production. This is a lightweight store
# for development / single-instance deployments.

_revocation_store: dict[str, dict] = {}  # id -> record
_credential_status: dict[str, str] = {}  # id -> "valid" | "revoked" | "expired"


def _get_status(item_id: str) -> str:
    """Return the current status for an ID."""
    if item_id in _revocation_store:
        return "revoked"
    return _credential_status.get(item_id, "valid")


# ── Endpoints ─────────────────────────────────────────────────────────


@revoke_router.post(
    "",
    response_model=RevokeResponse,
    summary="Revoke a token or credential",
)
async def revoke_item(
    body: RevokeRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
    _api_key: str = Depends(api_key_dependency),
):
    """Revoke a token or credential by its identifier.

    Requires an API key with admin privileges.
    """
    if not body.id.strip():
        raise HTTPException(status_code=400, detail="ID cannot be empty")

    now = utcnow()
    revoked_at_str = format_timestamp(now)

    _revocation_store[body.id] = {
        "id": body.id,
        "status": "revoked",
        "reason": body.reason,
        "revoked_at": revoked_at_str,
        "revoked_at_ts": int(time.time()),
    }
    _credential_status[body.id] = "revoked"

    logger.info("item_revoked", id=body.id, reason=body.reason)

    return RevokeResponse(
        id=body.id,
        status="revoked",
        revoked_at=revoked_at_str,
        request_id=request_id,
    )


@revoke_router.get(
    "/status/{item_id}",
    response_model=StatusResponse,
    summary="Check revocation status by ID",
)
async def check_status(
    item_id: str,
    request_id: str = Depends(request_id_dependency),
):
    """Check whether a specific token or credential has been revoked."""
    record = _revocation_store.get(item_id)

    if record:
        return StatusResponse(
            id=item_id,
            status="revoked",
            revoked_at=record.get("revoked_at"),
            reason=record.get("reason"),
            request_id=request_id,
        )

    # For items that were never revoked, indicate "valid"
    return StatusResponse(
        id=item_id,
        status=_credential_status.get(item_id, "valid"),
        request_id=request_id,
    )


@revoke_router.get(
    "/list",
    response_model=RevokeListResponse,
    summary="List all revoked credentials (paginated, admin-only)",
)
async def list_revoked(
    page: int = Query(default=1, ge=1, le=10000),
    per_page: int = Query(default=20, ge=1, le=100),
    request_id: str = Depends(request_id_dependency),
    _api_key: str = Depends(api_key_dependency),
):
    """Return a paginated list of all revoked credentials.

    Requires an API key with admin privileges.
    """
    revoked_items = [
        RevokeListItem(
            id=record["id"],
            status="revoked",
            reason=record.get("reason", ""),
            revoked_at=record["revoked_at"],
        )
        for record in _revocation_store.values()
    ]

    # Sort by revocation time descending (most recent first)
    revoked_items.sort(key=lambda x: x.revoked_at, reverse=True)

    total = len(revoked_items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = revoked_items[start:end]

    return RevokeListResponse(
        revoked=page_items,
        total=total,
        page=page,
        request_id=request_id,
    )


@revoke_router.post(
    "/bulk",
    response_model=BulkRevokeResponse,
    summary="Bulk-revoke multiple credentials",
)
async def bulk_revoke(
    body: BulkRevokeRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
    _api_key: str = Depends(api_key_dependency),
):
    """Revoke multiple tokens or credentials in a single request.

    Requires an API key with admin privileges.
    """
    now = utcnow()
    revoked_at_str = format_timestamp(now)
    now_ts = int(time.time())

    results: list[BulkRevokeItem] = []

    for item_id in body.ids:
        if not item_id.strip():
            continue

        _revocation_store[item_id] = {
            "id": item_id,
            "status": "revoked",
            "reason": body.reason,
            "revoked_at": revoked_at_str,
            "revoked_at_ts": now_ts,
        }
        _credential_status[item_id] = "revoked"

        results.append(
            BulkRevokeItem(id=item_id, status="revoked", revoked_at=revoked_at_str)
        )

    logger.info("bulk_revoke_completed", count=len(results), reason=body.reason)

    return BulkRevokeResponse(
        results=results,
        total=len(results),
        request_id=request_id,
    )


# ── W3C StatusList2021 compatible endpoint ────────────────────────────


@status_router.get(
    "/{item_id}",
    response_model=StatusResponse,
    summary="W3C StatusList2021 compatible status check",
)
async def status_list_check(
    item_id: str,
    request_id: str = Depends(request_id_dependency),
):
    """W3C StatusList2021 compatible status check.

    Returns the status of a token or credential in a format compatible
    with the W3C StatusList2021 specification.

    Response includes:
      - id: The credential/token identifier
      - status: "valid", "revoked", or "expired"
      - status_purpose: Always "revocation" for this endpoint
      - revoked_at: ISO 8601 timestamp if revoked
      - reason: Reason for revocation if applicable
    """
    return await check_status(item_id, request_id)


# ── Public utility (for use by other route modules) ───────────────────


def is_revoked(item_id: str) -> bool:
    """Check whether a given ID has been revoked.

    This is the function other route handlers (e.g. token verification)
    should call when verifying tokens or credentials.
    """
    return item_id in _revocation_store
