"""Webhook notification system for verification, revocation, and QR scan events."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from structlog import get_logger

from app.deps import api_key_dependency, rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError
from app.models.schemas import (
    WebhookRequest,
    WebhookResponse,
    WebhookListResponse,
    WebhookEventResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])

# In-memory store (use PostgreSQL in production)
_webhook_store: dict[str, dict] = {}
_webhook_events: list[dict] = []


# ── Webhook delivery ───────────────────────────────────────────────────────────


async def deliver_webhook(
    webhook_url: str,
    event_type: str,
    payload: dict,
    secret: str,
    event_id: str,
) -> bool:
    """Deliver a webhook event with HMAC-SHA256 signature.

    Uses the shared secret to sign the JSON body so the receiver can verify
    that the request genuinely came from VeilPass.
    """
    body = json.dumps(
        {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": format_timestamp(utcnow()),
            "data": payload,
        },
        separators=(",", ":"),
    )

    signature = hmac.new(
        secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-VeilPass-Event": event_type,
        "X-VeilPass-Signature": f"sha256={signature}",
        "X-VeilPass-Timestamp": str(int(time.time())),
        "X-VeilPass-Delivery": event_id,
        "User-Agent": "VeilPass-Webhook/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                webhook_url, json=json.loads(body), headers=headers
            )
            if 200 <= resp.status_code < 300:
                logger.info(
                    "webhook_delivered",
                    event_id=event_id,
                    webhook_url=webhook_url,
                    status=resp.status_code,
                )
                return True
            else:
                logger.warning(
                    "webhook_failed",
                    event_id=event_id,
                    webhook_url=webhook_url,
                    status=resp.status_code,
                    response_body=resp.text[:512],
                )
                return False
    except httpx.TimeoutException:
        logger.error("webhook_timeout", event_id=event_id, webhook_url=webhook_url)
        return False
    except httpx.RequestError as exc:
        logger.error(
            "webhook_request_error",
            event_id=event_id,
            webhook_url=webhook_url,
            error=str(exc),
        )
        return False
    except Exception as exc:
        logger.error(
            "webhook_unexpected_error",
            event_id=event_id,
            webhook_url=webhook_url,
            error=str(exc),
        )
        return False


async def trigger_webhooks(
    event_type: str,
    payload: dict,
    background_tasks: BackgroundTasks,
) -> None:
    """Trigger all active webhooks subscribed to *event_type*.

    This should be called from other route handlers (token issuance,
    verification, QR scan, etc.) via ``BackgroundTasks``.
    """
    event_id = generate_id()
    now = format_timestamp(utcnow())

    for wh_id, wh in _webhook_store.items():
        if not wh.get("active", True):
            continue
        if event_type not in wh.get("events", []):
            continue

        event = {
            "id": event_id,
            "webhook_id": wh_id,
            "event_type": event_type,
            "payload": payload,
            "status": "pending",
            "created_at": now,
        }
        _webhook_events.append(event)

        background_tasks.add_task(
            deliver_webhook,
            wh["url"],
            event_type,
            payload,
            wh.get("secret", ""),
            event_id,
        )

    if _webhook_store:
        logger.debug(
            "webhooks_triggered",
            event_type=event_type,
            event_id=event_id,
            subscriber_count=sum(
                1
                for wh in _webhook_store.values()
                if wh.get("active", True) and event_type in wh.get("events", [])
            ),
        )


# ── CRUD endpoints ─────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=WebhookResponse,
    summary="Register a webhook",
    status_code=201,
)
async def create_webhook(
    body: WebhookRequest,
    background_tasks: BackgroundTasks,
    _rate: None = Depends(rate_limit_dependency),
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> WebhookResponse:
    """Register a new webhook endpoint.

    The webhook will receive POST requests for each subscribed event type.
    Each delivery includes an HMAC-SHA256 signature header that can be used
    to verify the request authenticity.
    """
    if not body.url.startswith("https://"):
        raise InvalidInputError("Webhook URL must use HTTPS")

    wh_id = f"wh_{generate_id()}"
    now = format_timestamp(utcnow())

    _webhook_store[wh_id] = {
        "id": wh_id,
        "url": body.url,
        "events": list(dict.fromkeys(body.events)),  # deduplicate
        "secret": body.secret,
        "description": body.description or "",
        "active": True,
        "created_at": now,
        "updated_at": now,
    }

    logger.info(
        "webhook_created",
        webhook_id=wh_id,
        event_count=len(body.events),
    )

    # Send a test event to confirm the endpoint is reachable
    if background_tasks is not None:
        background_tasks.add_task(
            deliver_webhook,
            body.url,
            "test.ping",
            {"message": "Webhook registered successfully"},
            body.secret,
            f"test_{wh_id}",
        )

    return WebhookResponse(
        id=wh_id,
        url=body.url,
        events=_webhook_store[wh_id]["events"],
        active=True,
        created_at=now,
        updated_at=now,
        request_id=request_id,
    )


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="List registered webhooks",
)
async def list_webhooks(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> WebhookListResponse:
    """Return a paginated list of registered webhooks."""
    all_ids = sorted(_webhook_store.keys(), reverse=True)
    total = len(all_ids)
    start = (page - 1) * per_page
    end = start + per_page
    page_ids = all_ids[start:end]

    webhooks = []
    for wh_id in page_ids:
        wh = _webhook_store[wh_id]
        webhooks.append(
            WebhookResponse(
                id=wh_id,
                url=wh["url"],
                events=wh["events"],
                active=wh.get("active", True),
                created_at=wh["created_at"],
                updated_at=wh["updated_at"],
                request_id=request_id,
            )
        )

    return WebhookListResponse(
        webhooks=webhooks,
        total=total,
        request_id=request_id,
    )


@router.get(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Get webhook details",
)
async def get_webhook(
    webhook_id: str,
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> WebhookResponse:
    """Return details for a single webhook."""
    wh = _webhook_store.get(webhook_id)
    if wh is None:
        raise NotFoundError(f"Webhook not found: {webhook_id}")

    return WebhookResponse(
        id=webhook_id,
        url=wh["url"],
        events=wh["events"],
        active=wh.get("active", True),
        created_at=wh["created_at"],
        updated_at=wh["updated_at"],
        request_id=request_id,
    )


@router.put(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update a webhook",
)
async def update_webhook(
    webhook_id: str,
    body: WebhookRequest,
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> WebhookResponse:
    """Update an existing webhook's URL, events, secret, or description."""
    if webhook_id not in _webhook_store:
        raise NotFoundError(f"Webhook not found: {webhook_id}")

    if not body.url.startswith("https://"):
        raise InvalidInputError("Webhook URL must use HTTPS")

    now = format_timestamp(utcnow())
    _webhook_store[webhook_id].update(
        {
            "url": body.url,
            "events": list(dict.fromkeys(body.events)),
            "secret": body.secret,
            "description": body.description or "",
            "updated_at": now,
        }
    )

    logger.info("webhook_updated", webhook_id=webhook_id)

    wh = _webhook_store[webhook_id]
    return WebhookResponse(
        id=webhook_id,
        url=wh["url"],
        events=wh["events"],
        active=wh.get("active", True),
        created_at=wh["created_at"],
        updated_at=now,
        request_id=request_id,
    )


@router.delete(
    "/{webhook_id}",
    summary="Delete a webhook",
)
async def delete_webhook(
    webhook_id: str,
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> dict:
    """Delete a webhook by ID."""
    if webhook_id not in _webhook_store:
        raise NotFoundError(f"Webhook not found: {webhook_id}")

    del _webhook_store[webhook_id]

    logger.info("webhook_deleted", webhook_id=webhook_id)

    return {
        "success": True,
        "message": f"Webhook {webhook_id} deleted",
        "request_id": request_id,
    }


@router.post(
    "/{webhook_id}/test",
    summary="Send a test event to a webhook",
)
async def test_webhook(
    webhook_id: str,
    background_tasks: BackgroundTasks,
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> dict:
    """Send a ``test.ping`` event to verify connectivity."""
    wh = _webhook_store.get(webhook_id)
    if wh is None:
        raise NotFoundError(f"Webhook not found: {webhook_id}")

    test_event_id = f"test_{generate_id()}"
    background_tasks.add_task(
        deliver_webhook,
        wh["url"],
        "test.ping",
        {"message": "This is a test event from VeilPass"},
        wh.get("secret", ""),
        test_event_id,
    )

    return {
        "success": True,
        "message": "Test event dispatched",
        "event_id": test_event_id,
        "request_id": request_id,
    }


@router.get(
    "/{webhook_id}/events",
    response_model=list[WebhookEventResponse],
    summary="List recent events for a webhook",
)
async def list_webhook_events(
    webhook_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    _api_key: str = Depends(api_key_dependency),
    request_id: str = Depends(request_id_dependency),
) -> list[WebhookEventResponse]:
    """Return the most recent delivery events for a specific webhook."""
    if webhook_id not in _webhook_store:
        raise NotFoundError(f"Webhook not found: {webhook_id}")

    events = [
        WebhookEventResponse(
            id=e["id"],
            webhook_id=e["webhook_id"],
            event_type=e["event_type"],
            status=e.get("status", "unknown"),
            created_at=e["created_at"],
            request_id=request_id,
        )
        for e in _webhook_events
        if e["webhook_id"] == webhook_id
    ]

    return events[-limit:]
