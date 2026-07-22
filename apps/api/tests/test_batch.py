"""Tests for Batch Generation endpoints."""

import zipfile
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestBatchQR:
    """Test batch QR code generation."""

    def test_batch_generate_qr_zip(self):
        """Generate batch QR codes as ZIP and verify contents."""
        response = client.post(
            "/api/v1/qr/batch",
            json={
                "entries": [
                    {"content": "https://example.com/ticket/001", "filename": "ticket-001"},
                    {"content": "https://example.com/ticket/002", "filename": "ticket-002"},
                ],
                "format": "png",
                "ecl": "H",
                "size": 256,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        # Verify ZIP contents
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data, "r") as zf:
            names = zf.namelist()
            assert "ticket-001.png" in names
            assert "ticket-002.png" in names
            assert len(zf.read("ticket-001.png")) > 100

    def test_batch_generate_qr_svg(self):
        """Generate batch QR codes in SVG format."""
        response = client.post(
            "/api/v1/qr/batch",
            json={
                "entries": [
                    {"content": "https://example.com/svg-test"},
                ],
                "format": "svg",
            },
        )
        assert response.status_code == 200
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data, "r") as zf:
            assert "qr-0001.svg" in zf.namelist()
            content = zf.read("qr-0001.svg").decode("utf-8")
            assert "<svg" in content

    def test_batch_generate_qr_empty(self):
        """Batch with no entries should fail."""
        response = client.post(
            "/api/v1/qr/batch",
            json={"entries": []},
        )
        assert response.status_code == 400

    def test_batch_generate_qr_too_many(self):
        """Batch with too many entries should fail."""
        entries = [{"content": f"https://example.com/{i}"} for i in range(1001)]
        response = client.post(
            "/api/v1/qr/batch",
            json={"entries": entries},
        )
        assert response.status_code == 400


class TestBatchTokens:
    """Test batch token generation."""

    def test_batch_generate_tokens(self):
        """Generate multiple tokens in batch."""
        response = client.post(
            "/api/v1/token/batch",
            json={
                "entries": [
                    {"subject": "user-001", "claims": {"role": "admin"}},
                    {"subject": "user-002", "claims": {"role": "viewer"}},
                ],
                "ttl": 86400,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["tokens"]) == 2
        assert data["tokens"][0]["subject"] == "user-001"
        assert data["tokens"][1]["subject"] == "user-002"
        assert data["tokens"][0]["token"] is not None
        assert data["tokens"][1]["token"] is not None

    def test_batch_generate_tokens_empty(self):
        """Batch token generation with no entries should fail."""
        response = client.post(
            "/api/v1/token/batch",
            json={"entries": [], "ttl": 3600},
        )
        assert response.status_code == 400

    def test_batch_generate_tokens_too_many(self):
        """Batch token generation with too many entries should fail."""
        entries = [{"subject": f"user-{i}"} for i in range(101)]
        response = client.post(
            "/api/v1/token/batch",
            json={"entries": entries, "ttl": 3600},
        )
        assert response.status_code == 400


class TestBatchLinks:
    """Test batch signed link generation."""

    def test_batch_generate_links(self):
        """Generate multiple signed links in batch."""
        response = client.post(
            "/api/v1/link/batch",
            json={
                "entries": [
                    {"resource": "resource-001", "one_time": True},
                    {"resource": "resource-002", "one_time": False, "max_uses": 5},
                ],
                "ttl": 86400,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["links"]) == 2
        assert "claim.veilpass.app" in data["links"][0]["url"]
        assert "claim.veilpass.app" in data["links"][1]["url"]
        assert data["links"][0]["resource"] == "resource-001"

    def test_batch_generate_links_empty(self):
        """Batch link generation with no entries should fail."""
        response = client.post(
            "/api/v1/link/batch",
            json={"entries": [], "ttl": 3600},
        )
        assert response.status_code == 400


class TestBatchDynamicQR:
    """Test batch dynamic QR creation."""

    def test_batch_create_dynamic_qr(self):
        """Create multiple dynamic QRs in batch."""
        response = client.post(
            "/api/v1/dynamic-qr/batch",
            json={
                "entries": [
                    {"destination_url": "https://example.com/event-001", "title": "Event 1", "tags": ["event"]},
                    {"destination_url": "https://example.com/event-002", "title": "Event 2", "tags": ["event"]},
                ],
                "expires_in": 2592000,
                "max_scans": None,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["items"]) == 2
        assert data["items"][0]["id"].startswith("qr_")
        assert "veil.link/r/" in data["items"][0]["redirect_url"]

    def test_batch_create_dynamic_qr_empty(self):
        """Batch dynamic QR with no entries should fail."""
        response = client.post(
            "/api/v1/dynamic-qr/batch",
            json={"entries": []},
        )
        assert response.status_code == 400

    def test_batch_create_dynamic_qr_invalid_url(self):
        """Batch dynamic QR with invalid URL should be omitted."""
        response = client.post(
            "/api/v1/dynamic-qr/batch",
            json={
                "entries": [
                    {"destination_url": "https://example.com/valid"},
                    {"destination_url": "not-a-url"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Only the valid entry should be in items
        assert len(data["items"]) == 1
