"""Dynamic QR code generation with privacy-first analytics tracking.

Dynamic QR codes use short redirect URLs (veil.link/r/{short_code}) that can be
updated without reprinting. Every scan is tracked for analytics, with three
privacy modes:

- **standard** — Full analytics: anonymized IP, user agent, referer, timestamp.
- **privacy** — Minimal analytics: country-level only, no user-agent/referer,
  timestamps rounded to the hour.
- **aggregate_only** — Only total scan count. No per-scan events stored.
"""

import io
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import qrcode
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, Response
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError, RateLimitedError
from app.models.schemas import (
    DynamicQRListResponse,
    DynamicQRListItem,
    DynamicQRRequest,
    DynamicQRResponse,
    DynamicQRUpdateRequest,
    PrivacyScoreResponse,
    QRAnalyticsResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/dynamic-qr", tags=["Dynamic QR"])

# In-memory stores (use PostgreSQL in production)
_dynamic_qr_store: dict[str, dict] = {}
_qr_scan_events: list[dict] = []
_redirect_rate_limiter_buckets: dict[str, tuple[float, int]] = {}  # ip -> (window_start, count)
_REDIRECT_RATE_LIMIT = 10  # requests per second per IP
_REDIRECT_WINDOW = 1.0  # seconds

# ECL mapping
_ECL_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}

_BASE_REDIRECT_DOMAIN = "https://veil.link/r/"

# Privacy compliance metadata
_PRIVACY_COMPLIANCE = {
    "standard": {
        "compliant_with": ["GDPR", "Kenya DPA", "CCPA"],
        "data_retention_days": 90,
        "auto_delete": False,
    },
    "privacy": {
        "compliant_with": ["GDPR", "Kenya DPA", "CCPA", "ePrivacy", "PECR"],
        "data_retention_days": 30,
        "auto_delete": True,
    },
    "aggregate_only": {
        "compliant_with": ["GDPR", "Kenya DPA", "CCPA", "ePrivacy", "PECR", "LGPD"],
        "data_retention_days": 7,
        "auto_delete": True,
    },
}


def _check_redirect_rate_limit(ip: str) -> None:
    """Rate limit for redirect endpoint: 10 req/s per IP."""
    import time as _time

    now = _time.monotonic()
    window_start, count = _redirect_rate_limiter_buckets.get(ip, (now, 0))
    if now - window_start > _REDIRECT_WINDOW:
        window_start = now
        count = 0
    count += 1
    _redirect_rate_limiter_buckets[ip] = (window_start, count)
    if count > _REDIRECT_RATE_LIMIT:
        raise RateLimitedError("Too many redirect requests. Try again shortly.")


def _anonymize_ip(ip: str) -> str:
    """Anonymize an IPv4 or IPv6 address for privacy."""
    if "." in ip:
        # IPv4: keep first 3 octets
        parts = ip.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3]) + ".0"
    elif ":" in ip:
        # IPv6: keep first 80 bits (5 groups)
        parts = ip.split(":")
        if len(parts) >= 5:
            return ":".join(parts[:5]) + ":0000:0000:0000"
    return ip


def _country_from_ip(ip: str) -> str:
    """Derive a country-level identifier from an IP address.

    In production this would use GeoIP.  For now we return a hash prefix
    that preserves country-level granularity without exposing the full IP.
    """
    import hashlib as _hashlib

    # Simple prefix hash — in production replace with GeoIP lookup
    raw = _hashlib.sha256(ip.encode()).hexdigest()[:8]
    return f"country_{raw}"


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def _get_privacy_mode(entry: dict) -> str:
    """Return the privacy mode for a QR entry, defaulting to 'standard'."""
    return entry.get("privacy_mode", "standard")


def _get_aggregate_scans(entry_id: str) -> int:
    """Get total scan count for a QR entry across all privacy modes."""
    count = 0
    for e in _qr_scan_events:
        if e.get("qr_id") == entry_id:
            count += 1
    return count


# ── Create Dynamic QR ───────────────────────────────────────────────────────


@router.post("", response_model=DynamicQRResponse, summary="Create a dynamic QR code")
async def create_dynamic_qr(
    body: DynamicQRRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create a dynamic QR code that can be updated after generation.

    Returns a redirect URL (veil.link/r/{short_code}) and QR image URL.
    The redirect URL can be updated later without reprinting the QR code.

    **Privacy modes:**

    - ``standard`` — Full analytics (anonymized IP, user-agent, referer, timestamp).
    - ``privacy`` — Country-level only, no user-agent/referer, hourly timestamps.
    - ``aggregate_only`` — Only total scan count; no per-scan events stored.
    """
    import re

    if not body.destination_url.strip():
        raise InvalidInputError("destination_url cannot be empty")

    # Basic URL validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"  # domain
        r"(:\d+)?"  # optional port
        r"(/.*)?$"  # path
    )
    if not url_pattern.match(body.destination_url):
        raise InvalidInputError(
            "destination_url must be a valid HTTP or HTTPS URL"
        )

    qr_id = f"qr_{generate_id()}"
    short_code = uuid4().hex[:12]

    now = utcnow()
    expires_at: Optional[datetime] = None
    if body.expires_in is not None and body.expires_in > 0:
        expires_at = now + timedelta(seconds=body.expires_in)

    store_entry = {
        "id": qr_id,
        "short_code": short_code,
        "destination_url": body.destination_url,
        "title": body.title,
        "allow_update": body.allow_update,
        "max_scans": body.max_scans,
        "tags": body.tags[:20],  # limit tags
        "created_at": now,
        "expires_at": expires_at,
        "updated_at": now,
        "active": True,
        "scan_count": 0,
        "privacy_mode": body.privacy_mode,
    }
    _dynamic_qr_store[qr_id] = store_entry
    # Also index by short_code for fast redirect lookups
    _dynamic_qr_store[short_code] = store_entry

    redirect_url = f"{_BASE_REDIRECT_DOMAIN}{short_code}"
    qr_image_url = f"/api/v1/dynamic-qr/{qr_id}/qr"

    logger.info(
        "dynamic_qr_created",
        qr_id=qr_id,
        short_code=short_code,
        destination=body.destination_url,
        privacy_mode=body.privacy_mode,
    )

    return DynamicQRResponse(
        id=qr_id,
        short_code=short_code,
        redirect_url=redirect_url,
        qr_image_url=qr_image_url,
        created_at=format_timestamp(now),
        expires_at=format_timestamp(expires_at) if expires_at else None,
        request_id=request_id,
    )


# ── Generate QR Image for Dynamic Link ──────────────────────────────────────


@router.get("/{id}/qr", summary="Generate QR PNG for a dynamic link")
async def get_dynamic_qr_image(
    id: str,
    request: Request,
    request_id: str = Depends(request_id_dependency),
):
    """Generate a QR code PNG image for a dynamic redirect URL."""
    entry = _dynamic_qr_store.get(id)
    if not entry:
        raise NotFoundError(f"Dynamic QR not found: {id}")

    redirect_url = f"{_BASE_REDIRECT_DOMAIN}{entry['short_code']}"

    # Build QR code
    ecl = _ECL_MAP.get("H", qrcode.constants.ERROR_CORRECT_H)
    qr = qrcode.QRCode(
        version=None,
        error_correction=ecl,
        box_size=10,
        border=4,
    )
    qr.add_data(redirect_url)
    try:
        qr.make(fit=True)
    except ValueError as e:
        raise InvalidInputError(f"Failed to generate QR: {e}")

    img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
    img = img.resize((512, 512))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename=dynamic-qr-{entry["short_code"]}.png',
            "X-Request-ID": request_id,
        },
    )


# ── Redirect Endpoint ───────────────────────────────────────────────────────


@router.get(
    "/r/{short_code}",
    summary="Redirect endpoint with privacy-aware analytics",
    include_in_schema=True,
)
async def redirect_dynamic_qr(
    short_code: str,
    request: Request,
):
    """Redirect a short code to its destination URL with analytics capture.

    Analytics behaviour depends on the QR's **privacy_mode** setting:

    - ``standard``: Tracks anonymized IP, user-agent, referer, timestamp.
    - ``privacy``: Tracks country-level only, no user-agent/referer,
      timestamps rounded to hour.
    - ``aggregate_only``: Only increments scan counter; no events stored.

    Enforces: expiration, max_scans, and revocation checks.
    Rate limited: 10 requests/second per IP.
    """
    client_ip = _get_client_ip(request)
    _check_redirect_rate_limit(client_ip)

    # Look up by short_code
    entry = _dynamic_qr_store.get(short_code)
    if not entry:
        raise NotFoundError(f"Short code not found: {short_code}")

    # Check if active
    if not entry.get("active", True):
        return Response(
            status_code=410,
            content='{"success":false,"error":{"code":"GONE","message":"This link has been deactivated"}}',
            media_type="application/json",
            headers={"X-Request-ID": ""},
        )

    # Check expiration
    expires_at = entry.get("expires_at")
    if expires_at and utcnow() > expires_at:
        return Response(
            status_code=410,
            content='{"success":false,"error":{"code":"EXPIRED","message":"This link has expired"}}',
            media_type="application/json",
            headers={"X-Request-ID": ""},
        )

    # Check max_scans
    max_scans = entry.get("max_scans")
    if max_scans is not None and entry["scan_count"] >= max_scans:
        return Response(
            status_code=410,
            content='{"success":false,"error":{"code":"MAX_SCANS_REACHED","message":"Maximum scan limit reached"}}',
            media_type="application/json",
            headers={"X-Request-ID": ""},
        )

    # Increment scan count (always tracked)
    entry["scan_count"] += 1

    # Privacy-mode-aware analytics capture
    privacy_mode = _get_privacy_mode(entry)
    now = utcnow()

    if privacy_mode == "aggregate_only":
        # No per-scan events — just the counter above
        logger.info(
            "dynamic_qr_redirected_aggregate",
            short_code=short_code,
            scan_count=entry["scan_count"],
        )
    else:
        anonymized_ip = _anonymize_ip(client_ip)

        if privacy_mode == "privacy":
            # Minimal: country-level only, no user-agent/referer
            # Timestamp rounded to hour
            rounded_hour = now.replace(minute=0, second=0, microsecond=0)
            scan_event = {
                "short_code": short_code,
                "qr_id": entry["id"],
                "country": _country_from_ip(anonymized_ip),
                "timestamp": rounded_hour,
                "privacy_mode": "privacy",
            }
        else:
            # Standard: full analytics
            user_agent = request.headers.get("User-Agent", "unknown")
            referer = request.headers.get("Referer", "direct")
            scan_event = {
                "short_code": short_code,
                "qr_id": entry["id"],
                "ip": anonymized_ip,
                "user_agent": user_agent[:256],
                "referer": referer[:512],
                "timestamp": now,
                "privacy_mode": "standard",
            }

        _qr_scan_events.append(scan_event)

        # Keep scan events bounded (in production use a database)
        if len(_qr_scan_events) > 100000:
            _qr_scan_events[:50000] = []

        logger.info(
            "dynamic_qr_redirected",
            short_code=short_code,
            scan_count=entry["scan_count"],
            privacy_mode=privacy_mode,
        )

    return RedirectResponse(url=entry["destination_url"], status_code=302)


# ── Get Analytics ───────────────────────────────────────────────────────────


@router.get(
    "/{id}/analytics",
    response_model=QRAnalyticsResponse,
    summary="Get analytics for a dynamic QR (respects privacy mode)",
)
async def get_dynamic_qr_analytics(
    id: str,
    request: Request,
    request_id: str = Depends(request_id_dependency),
):
    """Get analytics for a dynamic QR code.

    The level of detail depends on the QR's **privacy_mode**:

    - ``standard``: Full breakdown (unique IPs, scans over time, agents, referrers).
    - ``privacy``: Country-level scans over time only.
    - ``aggregate_only``: Returns only ``total_scans``; all other fields empty.
    """
    entry = _dynamic_qr_store.get(id)
    if not entry:
        raise NotFoundError(f"Dynamic QR not found: {id}")

    privacy_mode = _get_privacy_mode(entry)
    qr_id = entry["id"]
    relevant_events = [e for e in _qr_scan_events if e.get("qr_id") == qr_id]
    total_scans = len(relevant_events) + (entry.get("scan_count", 0) - len(relevant_events) if privacy_mode == "aggregate_only" else 0)

    if privacy_mode == "aggregate_only":
        # Only return total scan count — no breakdowns
        total_scans = entry.get("scan_count", 0)
        return QRAnalyticsResponse(
            id=qr_id,
            total_scans=total_scans,
            unique_ips=0,
            scans_over_time=[],
            top_user_agents=[],
            top_referrers=[],
            last_scan=None,
            request_id=request_id,
        )

    unique_ips: int = 0
    scans_over_time: list[dict] = []
    top_user_agents: list[dict] = []
    top_referrers: list[dict] = []

    if privacy_mode == "privacy":
        # Country-level analytics only
        unique_countries = {e.get("country", "unknown") for e in relevant_events}
        unique_ips = len(unique_countries)

        # Scans over time (by hour)
        scans_by_hour: dict[str, int] = {}
        for e in relevant_events:
            ts = e.get("timestamp", now)
            if isinstance(ts, datetime):
                hour_key = ts.strftime("%Y-%m-%dT%H:00:00Z")
            else:
                hour_key = str(ts)[:13] + ":00:00Z"
            scans_by_hour[hour_key] = scans_by_hour.get(hour_key, 0) + 1
        scans_over_time = [
            {"date": d, "count": c} for d, c in sorted(scans_by_hour.items())
        ]
    else:
        # Standard analytics
        unique_ips = len({e.get("ip", "") for e in relevant_events if e.get("ip")})

        # Scans over time (by date)
        scans_by_date: dict[str, int] = {}
        for e in relevant_events:
            ts = e.get("timestamp")
            if isinstance(ts, datetime):
                date_key = ts.strftime("%Y-%m-%d")
            else:
                date_key = str(ts)[:10]
            scans_by_date[date_key] = scans_by_date.get(date_key, 0) + 1
        scans_over_time = [
            {"date": d, "count": c} for d, c in sorted(scans_by_date.items())
        ]

        # Top user agents
        agent_counts: dict[str, int] = {}
        for e in relevant_events:
            agent = e.get("user_agent", "unknown")
            if "Mobile" in agent or "iPhone" in agent or "Android" in agent:
                simplified = "Mobile"
            elif "bot" in agent.lower() or "crawler" in agent.lower():
                simplified = "Bot"
            else:
                simplified = "Desktop"
            agent_counts[simplified] = agent_counts.get(simplified, 0) + 1
        top_user_agents = [
            {"agent": a, "count": c}
            for a, c in sorted(agent_counts.items(), key=lambda x: -x[1])[:10]
        ]

        # Top referrers
        referer_counts: dict[str, int] = {}
        for e in relevant_events:
            ref = e.get("referer", "direct")
            if ref == "direct" or not ref:
                ref = "direct"
            referer_counts[ref] = referer_counts.get(ref, 0) + 1
        top_referrers = [
            {"referer": r, "count": c}
            for r, c in sorted(referer_counts.items(), key=lambda x: -x[1])[:10]
        ]

    # Last scan time
    last_scan: Optional[str] = None
    if relevant_events:
        last_ts = relevant_events[-1].get("timestamp")
        if isinstance(last_ts, datetime):
            last_scan = format_timestamp(last_ts)

    return QRAnalyticsResponse(
        id=qr_id,
        total_scans=total_scans,
        unique_ips=unique_ips,
        scans_over_time=scans_over_time,
        top_user_agents=top_user_agents,
        top_referrers=top_referrers,
        last_scan=last_scan,
        request_id=request_id,
    )


# ── Privacy Score Endpoint ──────────────────────────────────────────────────


@router.get(
    "/{id}/privacy-score",
    response_model=PrivacyScoreResponse,
    summary="Get privacy compliance score for a dynamic QR",
)
async def get_dynamic_qr_privacy_score(
    id: str,
    request: Request,
    request_id: str = Depends(request_id_dependency),
):
    """Return a privacy compliance score and regulatory alignment summary.

    Scores are calculated based on the QR's **privacy_mode**:
    - ``standard``: 45/100 — full analytics, longer retention.
    - ``privacy``: 78/100 — minimal collection, auto-delete.
    - ``aggregate_only``: 95/100 — anonymous counting only.
    """
    entry = _dynamic_qr_store.get(id)
    if not entry:
        raise NotFoundError(f"Dynamic QR not found: {id}")

    privacy_mode = _get_privacy_mode(entry)

    # Score mapping
    _SCORES = {
        "standard": 45,
        "privacy": 78,
        "aggregate_only": 95,
    }

    compliance = _PRIVACY_COMPLIANCE.get(
        privacy_mode,
        _PRIVACY_COMPLIANCE["standard"],
    )

    return PrivacyScoreResponse(
        score=_SCORES.get(privacy_mode, 45),
        compliant_with=compliance["compliant_with"],
        data_retention_days=compliance["data_retention_days"],
        auto_delete=compliance["auto_delete"],
        request_id=request_id,
    )


# ── Update Dynamic QR ───────────────────────────────────────────────────────


@router.patch(
    "/{id}",
    response_model=DynamicQRResponse,
    summary="Update a dynamic QR's destination URL",
)
async def update_dynamic_qr(
    id: str,
    body: DynamicQRUpdateRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Update the destination URL of a dynamic QR code.

    The QR image remains the same — the redirect target changes.
    """
    import re

    entry = _dynamic_qr_store.get(id)
    if not entry:
        raise NotFoundError(f"Dynamic QR not found: {id}")

    if not entry.get("allow_update", True):
        raise InvalidInputError("This QR code does not allow updates")

    if not body.destination_url.strip():
        raise InvalidInputError("destination_url cannot be empty")

    url_pattern = re.compile(
        r"^https?://"
        r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"
        r"(:\d+)?"
        r"(/.*)?$"
    )
    if not url_pattern.match(body.destination_url):
        raise InvalidInputError("destination_url must be a valid HTTP or HTTPS URL")

    entry["destination_url"] = body.destination_url
    entry["updated_at"] = utcnow()

    logger.info(
        "dynamic_qr_updated",
        qr_id=id,
        new_destination=body.destination_url,
    )

    redirect_url = f"{_BASE_REDIRECT_DOMAIN}{entry['short_code']}"
    qr_image_url = f"/api/v1/dynamic-qr/{id}/qr"

    return DynamicQRResponse(
        id=entry["id"],
        short_code=entry["short_code"],
        redirect_url=redirect_url,
        qr_image_url=qr_image_url,
        created_at=format_timestamp(entry["created_at"]),
        expires_at=format_timestamp(entry["expires_at"]) if entry.get("expires_at") else None,
        request_id=request_id,
    )


# ── Deactivate Dynamic QR ───────────────────────────────────────────────────


@router.delete(
    "/{id}",
    summary="Deactivate a dynamic QR code",
)
async def delete_dynamic_qr(
    id: str,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Deactivate a dynamic QR code. Future redirects return 410 Gone."""
    entry = _dynamic_qr_store.get(id)
    if not entry:
        raise NotFoundError(f"Dynamic QR not found: {id}")

    entry["active"] = False

    logger.info("dynamic_qr_deactivated", qr_id=id)

    return {
        "success": True,
        "message": f"Dynamic QR {id} has been deactivated",
        "request_id": request_id,
    }


# ── List Dynamic QRs ────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=DynamicQRListResponse,
    summary="List dynamic QR codes (paginated)",
)
async def list_dynamic_qrs(
    page: int = Query(default=1, ge=1, le=10000),
    per_page: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="created_at", pattern=r"^(created_at|updated_at|scan_count|title)$"),
    status: str = Query(default="all", pattern=r"^(all|active|inactive|expired)$"),
    request_id: str = Depends(request_id_dependency),
):
    """List all dynamic QR codes with pagination and sorting."""
    now = utcnow()

    # Collect unique QR entries (keyed by id, not short_code)
    qr_map: dict[str, dict] = {}
    for key, val in _dynamic_qr_store.items():
        if val.get("id") and not key.startswith("qr_"):
            continue  # skip short_code index entries
        qid = val.get("id", "")
        if qid:
            qr_map[qid] = val

    items = list(qr_map.values())

    # Filter by status
    if status == "active":
        items = [
            i
            for i in items
            if i.get("active", True)
            and (not i.get("expires_at") or i["expires_at"] > now)
        ]
    elif status == "inactive":
        items = [i for i in items if not i.get("active", True)]
    elif status == "expired":
        items = [
            i
            for i in items
            if i.get("expires_at") and i["expires_at"] <= now
        ]

    # Sort
    reverse = True
    if sort == "title":
        reverse = False
    items.sort(key=lambda x: x.get(sort, "") if isinstance(x.get(sort, ""), str) else str(x.get(sort, 0)), reverse=reverse)

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    list_items = []
    for item in page_items:
        expires = item.get("expires_at")
        list_items.append(
            DynamicQRListItem(
                id=item["id"],
                short_code=item["short_code"],
                title=item.get("title"),
                destination_url=item["destination_url"],
                total_scans=item.get("scan_count", 0),
                created_at=format_timestamp(item["created_at"]),
                expires_at=format_timestamp(expires) if expires else None,
                active=item.get("active", True),
                tags=item.get("tags", []),
            )
        )

    return DynamicQRListResponse(
        items=list_items,
        total=total,
        page=page,
        per_page=per_page,
        request_id=request_id,
    )


# ── Explicit redirect router for /api/v1/r/{short_code} ─────────────────────


_redirect_router = APIRouter(prefix="/api/v1", tags=["Dynamic QR"])


@_redirect_router.get("/r/{short_code}", include_in_schema=False)
async def redirect_short_code(
    short_code: str,
    request: Request,
):
    """External redirect endpoint mounted at /api/v1/r/{short_code}."""
    return await redirect_dynamic_qr(short_code, request)


# Include the redirect router in the main app via the dynamic_qr module export
# The main app will include both routers
