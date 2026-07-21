"""Health check endpoint for VeilPass API."""

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse
from app.utils import utcnow, format_timestamp

router = APIRouter(tags=["Health"])


@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check():
    """Return API health status, version, and current timestamp."""
    return HealthResponse(
        status="ok",
        version=settings.version,
        timestamp=format_timestamp(utcnow()),
    )
