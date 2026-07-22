"""Test fixtures and configuration for VeilPass API tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter buckets before each test."""
    from app.deps import _rate_limiter

    _rate_limiter.buckets.clear()
    yield


@pytest.fixture(autouse=True)
def reset_redirect_rate_limiter():
    """Reset the redirect endpoint rate limiter before each test."""
    from app.routes.dynamic_qr import _redirect_rate_limiter_buckets

    _redirect_rate_limiter_buckets.clear()
    yield


@pytest.fixture(autouse=True)
def reset_dynamic_qr_store():
    """Reset the in-memory dynamic QR store before each test."""
    from app.routes.dynamic_qr import _dynamic_qr_store, _qr_scan_events

    _dynamic_qr_store.clear()
    _qr_scan_events.clear()
    yield


@pytest.fixture(autouse=True)
def reset_batch_store():
    """Reset the batch dynamic QR store before each test."""
    from app.routes.batch import _dynamic_qr_store, _batch_jobs

    _dynamic_qr_store.clear()
    _batch_jobs.clear()
    yield


@pytest.fixture(autouse=True)
def reset_template_store():
    """Reset the in-memory template store before each test."""
    from app.routes.templates import _template_store

    _template_store.clear()
    yield


@pytest.fixture(scope="session")
def api_key() -> str:
    """Create a test API key."""
    from app.utils import generate_id

    return f"vp_test_{generate_id()}{generate_id()}"


@pytest.fixture
def auth_headers(api_key: str) -> dict[str, str]:
    """Authorization headers for API key authenticated endpoints."""
    return {"Authorization": f"Bearer {api_key}"}
