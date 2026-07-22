"""Immutable audit logging for all credential operations.

Provides an append-only audit trail that records every significant state
change (token issuance, verification, key rotation, etc.) together with the
actor, resource, and IP address for accountability.

In production this module should be backed by an append-only PostgreSQL table
or a dedicated audit-log store.
"""

import csv
import io
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from structlog import get_logger

from app.deps import api_key_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import AuditLogResponse, AuditLogListResponse
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])

# In-memory append-only audit store (use PostgreSQL in production)
_audit_log: list[dict] = []


# ── Audit helper ───────────────────────────────────────────────────────────────


async def log_audit_event(
    event_type: str,
    actor: str,
    resource_id: str,
    action: str,
    details: dict[str, Any] = None,
    ip_address: str = "",
    request_id: str = "",
) -> str:
    """Append an immutable entry to the audit log.

    Returns the unique audit entry ID.

    Parameters
    ----------
    event_type:
        A dotted event type such as ``token.issued``, ``key.rotated``, etc.
    actor:
        The entity that performed the action (API key ID, user ID, system).
    resource_id:
        The primary identifier of the affected resource (token ID, key ID, …).
    action:
        A verb describing the operation: ``create``, ``verify``, ``revoke``,
        ``rotate``, ``delete``.
    details:
        Arbitrary JSON-serialisable metadata captured at the time of the event.
    ip_address:
        The client IP address that triggered the event, if available.
    request_id:
        The HTTP request ID for correlation.
    """
    entry: dict[str, Any] = {
        "id": f"aud_{generate_id()}",
        "event_type": event_type,
        "actor": actor,
        "resource_id": resource_id,
        "action": action,
        "details": details or {},
        "ip_address": ip_address,
        "timestamp": format_timestamp(utcnow()),
        "request_id": request_id,
    }
    _audit_log.append(entry)
    logger.info("audit_event", **entry)
    return entry["id"]


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="List audit log entries",
)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    event_type: Optional[str] = Query(default=None),
    actor: Optional[str] = Query(default=None),
    resource_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    sort: str = Query(default="desc", pattern=r"^(asc|desc)$"),
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> AuditLogListResponse:
    """Return paginated, filterable audit log entries.

    Results are sorted by timestamp descending by default. Supports filtering
    by event type, actor, resource, action, and date range.
    """
    entries = list(_audit_log)

    # ── Filtering ──────────────────────────────────────────────────────────
    if event_type:
        entries = [e for e in entries if e["event_type"] == event_type]
    if actor:
        entries = [e for e in entries if e["actor"] == actor]
    if resource_id:
        entries = [e for e in entries if e["resource_id"] == resource_id]
    if action:
        entries = [e for e in entries if e["action"] == action]
    if from_date:
        entries = [e for e in entries if e["timestamp"] >= from_date]
    if to_date:
        entries = [e for e in entries if e["timestamp"] <= to_date]

    # ── Sorting ────────────────────────────────────────────────────────────
    entries.sort(key=lambda e: e["timestamp"], reverse=(sort == "desc"))

    # ── Pagination ─────────────────────────────────────────────────────────
    total = len(entries)
    start = (page - 1) * per_page
    end = start + per_page
    page_entries = entries[start:end]

    return AuditLogListResponse(
        entries=[
            AuditLogResponse(
                id=e["id"],
                event_type=e["event_type"],
                actor=e["actor"],
                resource_id=e["resource_id"],
                action=e["action"],
                details=e.get("details", {}),
                ip_address=e.get("ip_address", ""),
                timestamp=e["timestamp"],
                request_id=request_id,
            )
            for e in page_entries
        ],
        total=total,
        page=page,
        request_id=request_id,
    )


@router.get(
    "/export",
    summary="Export audit logs as CSV",
)
async def export_audit_logs(
    event_type: Optional[str] = Query(default=None),
    actor: Optional[str] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> StreamingResponse:
    """Download audit log entries as a CSV file.

    Supports the same filters as the list endpoint. The CSV contains all
    matching entries without pagination limits.
    """
    entries = list(_audit_log)

    if event_type:
        entries = [e for e in entries if e["event_type"] == event_type]
    if actor:
        entries = [e for e in entries if e["actor"] == actor]
    if from_date:
        entries = [e for e in entries if e["timestamp"] >= from_date]
    if to_date:
        entries = [e for e in entries if e["timestamp"] <= to_date]

    entries.sort(key=lambda e: e["timestamp"], reverse=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "event_type",
            "actor",
            "resource_id",
            "action",
            "details",
            "ip_address",
            "timestamp",
            "request_id",
        ]
    )
    for e in entries:
        writer.writerow(
            [
                e["id"],
                e["event_type"],
                e["actor"],
                e["resource_id"],
                e["action"],
                str(e.get("details", {})),
                e.get("ip_address", ""),
                e["timestamp"],
                e.get("request_id", ""),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=veilpass_audit_log.csv",
            "X-Request-ID": request_id,
        },
    )


@router.get(
    "/stats",
    summary="Audit log statistics",
)
async def audit_stats(
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> dict:
    """Return aggregate statistics from the audit log.

    Includes event counts per type, top actors, and daily breakdown for the
    last 30 days.
    """
    from collections import Counter, defaultdict

    today = utcnow()
    thirty_days_ago = today.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - __import__("datetime").timedelta(days=30)
    threshold = format_timestamp(thirty_days_ago)

    # Events per type
    type_counter: Counter = Counter()
    actor_counter: Counter = Counter()
    daily_counter: Counter = Counter()

    for e in _audit_log:
        type_counter[e["event_type"]] += 1
        actor_counter[e["actor"]] += 1
        ts = e.get("timestamp", "")
        if ts >= threshold:
            day = ts[:10]  # YYYY-MM-DD
            daily_counter[day] += 1

    return {
        "success": True,
        "total_events": len(_audit_log),
        "events_by_type": dict(type_counter.most_common(20)),
        "top_actors": [
            {"actor": actor, "count": count}
            for actor, count in actor_counter.most_common(10)
        ],
        "events_per_day": dict(sorted(daily_counter.items())),
        "request_id": request_id,
    }
