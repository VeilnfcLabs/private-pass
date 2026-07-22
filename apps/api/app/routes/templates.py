"""Template system for reusable credential configurations.

Templates define reusable configurations for signed-links, signed-urls,
tokens, QR codes, and NFC payloads. They support variable substitution
and version tracking.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError
from app.models.schemas import (
    TemplateListResponse,
    TemplatePreviewResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateRequest,
    TemplateResponse,
)
from app.utils import generate_id, format_timestamp, utcnow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])

# In-memory store (use PostgreSQL in production)
_template_store: dict[str, dict] = {}


def _validate_type_config(template_type: str, config: dict) -> None:
    """Validate template config based on type."""
    if template_type == "signed-link":
        if "ttl" in config and (not isinstance(config["ttl"], (int, float)) or config["ttl"] < 0):
            raise InvalidInputError("signed-link config.ttl must be a non-negative integer")
    elif template_type == "signed-url":
        if "expires_in" in config and (not isinstance(config["expires_in"], (int, float)) or config["expires_in"] < 0):
            raise InvalidInputError("signed-url config.expires_in must be a non-negative integer")
    elif template_type == "token":
        if "ttl" in config and (not isinstance(config["ttl"], (int, float)) or config["ttl"] < 0):
            raise InvalidInputError("token config.ttl must be a non-negative integer")
    elif template_type == "qr":
        if "format" in config and config["format"] not in ("png", "svg"):
            raise InvalidInputError("qr config.format must be 'png' or 'svg'")
        if "ecl" in config and config["ecl"] not in ("L", "M", "Q", "H"):
            raise InvalidInputError("qr config.ecl must be one of L, M, Q, H")
    elif template_type == "nfc":
        if "type" in config and config["type"] not in ("uri", "text", "phone", "email", "wifi", "custom"):
            raise InvalidInputError("nfc config.type must be a valid NFC type")


def _apply_variables(template: str, variables: dict[str, str]) -> str:
    """Apply variable substitution to a template string.

    Supports built-in variables: {now}, {uuid}, {date}, {time}
    and custom variables defined in the render request.
    """
    import uuid as _uuid

    builtins = {
        "now": format_timestamp(utcnow()),
        "uuid": _uuid.uuid4().hex,
        "date": utcnow().strftime("%Y-%m-%d"),
        "time": utcnow().strftime("%H:%M:%S"),
    }
    all_vars = {**builtins, **variables}

    result = template
    for key, value in all_vars.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def _render_content_based(
    config: dict,
    variables: dict[str, str],
    template_type: str,
) -> dict[str, Any]:
    """Render a content string from config with variable substitution."""
    result = {"type": template_type, "config": config}

    # Apply variable substitution to all string values in config
    rendered_config = {}
    for key, value in config.items():
        if isinstance(value, str):
            rendered_config[key] = _apply_variables(value, variables)
        elif isinstance(value, dict):
            rendered_config[key] = {
                k: _apply_variables(v, variables) if isinstance(v, str) else v
                for k, v in value.items()
            }
        elif isinstance(value, list):
            rendered_config[key] = [
                _apply_variables(item, variables) if isinstance(item, str) else item
                for item in value
            ]
        else:
            rendered_config[key] = value

    result["rendered_config"] = rendered_config

    # Build example output based on type
    if template_type == "signed-link":
        result["rendered"] = {
            "resource": rendered_config.get("resource", "example-resource"),
            "ttl": rendered_config.get("ttl", 86400),
            "one_time": rendered_config.get("one_time", True),
        }
    elif template_type == "signed-url":
        result["rendered"] = {
            "url": rendered_config.get("url", "https://example.com/resource"),
            "expires_in": rendered_config.get("expires_in", 3600),
            "permissions": rendered_config.get("permissions", "read"),
        }
    elif template_type == "token":
        result["rendered"] = {
            "subject": rendered_config.get("subject", "example-user"),
            "ttl": rendered_config.get("ttl", 86400),
            "claims": rendered_config.get("claims", {}),
        }
    elif template_type == "qr":
        result["rendered"] = {
            "content": rendered_config.get("content", "https://example.com"),
            "format": rendered_config.get("format", "png"),
            "ecl": rendered_config.get("ecl", "H"),
            "size": rendered_config.get("size", 512),
        }
    elif template_type == "nfc":
        result["rendered"] = {
            "payload": rendered_config.get("payload", "example-payload"),
            "type": rendered_config.get("type", "uri"),
        }

    return result


# ── Create Template ─────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=TemplateResponse,
    summary="Create a credential template",
)
async def create_template(
    body: TemplateRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Create a reusable template for credential generation.

    Templates define the configuration for signed-links, signed-urls,
    tokens, QR codes, or NFC payloads. They support variable substitution
    using {variable_name} syntax.
    """
    if not body.name.strip():
        raise InvalidInputError("Template name cannot be empty")

    if not body.config:
        raise InvalidInputError("Template config cannot be empty")

    # Validate type-specific config
    _validate_type_config(body.type, body.config)

    template_id = f"tpl_{generate_id()}"
    now = utcnow()

    template_entry = {
        "id": template_id,
        "name": body.name.strip(),
        "description": body.description,
        "type": body.type,
        "config": body.config,
        "version": 1,
        "tags": body.tags[:20],
        "created_at": now,
        "updated_at": now,
    }
    _template_store[template_id] = template_entry

    logger.info(
        "template_created",
        template_id=template_id,
        template_type=body.type,
        version=1,
    )

    return TemplateResponse(
        id=template_id,
        name=body.name.strip(),
        description=body.description,
        type=body.type,
        config=body.config,
        version=1,
        tags=body.tags[:20],
        created_at=format_timestamp(now),
        updated_at=format_timestamp(now),
        request_id=request_id,
    )


# ── List Templates ──────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=TemplateListResponse,
    summary="List templates (paginated)",
)
async def list_templates(
    page: int = Query(default=1, ge=1, le=10000),
    per_page: int = Query(default=20, ge=1, le=100),
    type: str = Query(default="", pattern=r"^(signed-link|signed-url|token|qr|nfc|)$"),
    request_id: str = Depends(request_id_dependency),
):
    """List all credential templates with pagination and optional type filter."""
    items = list(_template_store.values())

    if type:
        items = [i for i in items if i["type"] == type]

    items.sort(key=lambda x: x["created_at"], reverse=True)

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    templates = []
    for item in page_items:
        templates.append(
            TemplateResponse(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                type=item["type"],
                config=item["config"],
                version=item["version"],
                tags=item.get("tags", []),
                created_at=format_timestamp(item["created_at"]),
                updated_at=format_timestamp(item["updated_at"]),
                request_id=request_id,
            )
        )

    return TemplateListResponse(
        templates=templates,
        total=total,
        page=page,
        per_page=per_page,
        request_id=request_id,
    )


# ── Get Template Detail ─────────────────────────────────────────────────────


@router.get(
    "/{id}",
    response_model=TemplateResponse,
    summary="Get template details",
)
async def get_template(
    id: str,
    request_id: str = Depends(request_id_dependency),
):
    """Get the full details of a specific template."""
    entry = _template_store.get(id)
    if not entry:
        raise NotFoundError(f"Template not found: {id}")

    return TemplateResponse(
        id=entry["id"],
        name=entry["name"],
        description=entry.get("description"),
        type=entry["type"],
        config=entry["config"],
        version=entry["version"],
        tags=entry.get("tags", []),
        created_at=format_timestamp(entry["created_at"]),
        updated_at=format_timestamp(entry["updated_at"]),
        request_id=request_id,
    )


# ── Update Template ─────────────────────────────────────────────────────────


@router.put(
    "/{id}",
    response_model=TemplateResponse,
    summary="Update a template",
)
async def update_template(
    id: str,
    body: TemplateRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Update an existing template. Increments the version number.

    Changing the template type is not allowed.
    """
    entry = _template_store.get(id)
    if not entry:
        raise NotFoundError(f"Template not found: {id}")

    if entry["type"] != body.type:
        raise InvalidInputError(
            f"Cannot change template type from '{entry['type']}' to '{body.type}'"
        )

    if not body.name.strip():
        raise InvalidInputError("Template name cannot be empty")

    if not body.config:
        raise InvalidInputError("Template config cannot be empty")

    _validate_type_config(body.type, body.config)

    now = utcnow()
    entry["name"] = body.name.strip()
    entry["description"] = body.description
    entry["config"] = body.config
    entry["version"] += 1
    entry["tags"] = body.tags[:20]
    entry["updated_at"] = now

    logger.info(
        "template_updated",
        template_id=id,
        new_version=entry["version"],
    )

    return TemplateResponse(
        id=entry["id"],
        name=entry["name"],
        description=entry.get("description"),
        type=entry["type"],
        config=entry["config"],
        version=entry["version"],
        tags=entry.get("tags", []),
        created_at=format_timestamp(entry["created_at"]),
        updated_at=format_timestamp(now),
        request_id=request_id,
    )


# ── Delete Template ─────────────────────────────────────────────────────────


@router.delete(
    "/{id}",
    summary="Delete a template",
)
async def delete_template(
    id: str,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Delete a template permanently."""
    entry = _template_store.get(id)
    if not entry:
        raise NotFoundError(f"Template not found: {id}")

    del _template_store[id]

    logger.info("template_deleted", template_id=id)

    return {
        "success": True,
        "message": f"Template {id} has been deleted",
        "request_id": request_id,
    }


# ── Render Template ─────────────────────────────────────────────────────────


@router.post(
    "/{id}/render",
    response_model=TemplateRenderResponse,
    summary="Render a template with variables",
)
async def render_template(
    id: str,
    body: TemplateRenderRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Render a template with provided variables.

    Variables are substituted into the template config using {variable_name}
    syntax. Built-in variables {now}, {uuid}, {date}, and {time} are always
    available.
    """
    entry = _template_store.get(id)
    if not entry:
        raise NotFoundError(f"Template not found: {id}")

    result = _render_content_based(entry["config"], body.variables, entry["type"])

    logger.info(
        "template_rendered",
        template_id=id,
        variables=list(body.variables.keys()),
    )

    return TemplateRenderResponse(
        id=id,
        type=entry["type"],
        rendered=result,
        request_id=request_id,
    )


# ── Preview Template ────────────────────────────────────────────────────────


@router.get(
    "/{id}/preview",
    response_model=TemplatePreviewResponse,
    summary="Preview template output with example data",
)
async def preview_template(
    id: str,
    request_id: str = Depends(request_id_dependency),
):
    """Preview a template with example data.

    Generates example output based on the template configuration,
    using sample variables to demonstrate the rendered result.
    """
    entry = _template_store.get(id)
    if not entry:
        raise NotFoundError(f"Template not found: {id}")

    # Generate example variables based on template type
    example_variables: dict[str, str] = {}

    fields = entry["config"].get("fields", [])
    for field in fields:
        if isinstance(field, str):
            example_variables[field] = f"example-{field}"

    required_fields = entry["config"].get("required_fields", [])
    for field in required_fields:
        if isinstance(field, str):
            example_variables[field] = example_variables.get(field, f"required-{field}")

    # Add type-specific examples
    if entry["type"] == "signed-link":
        example_variables.setdefault("resource", "example-resource-id")
    elif entry["type"] == "signed-url":
        example_variables.setdefault("url", "https://example.com/protected-file.pdf")
    elif entry["type"] == "token":
        example_variables.setdefault("subject", "example-user")
    elif entry["type"] == "qr":
        example_variables.setdefault("content", "https://example.com/ticket")
    elif entry["type"] == "nfc":
        example_variables.setdefault("payload", "example-payload-data")

    result = _render_content_based(entry["config"], example_variables, entry["type"])

    return TemplatePreviewResponse(
        id=id,
        name=entry["name"],
        type=entry["type"],
        preview=result,
        request_id=request_id,
    )
