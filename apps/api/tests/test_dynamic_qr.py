"""Tests for Dynamic QR with Analytics endpoints."""

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestDynamicQR:
    """Test Dynamic QR creation, redirect, analytics, and management."""

    def _create_dynamic_qr(self, **overrides):
        """Helper: create a dynamic QR and return the response data."""
        payload = {
            "destination_url": "https://example.com/ticket-123",
            "title": "Conference Ticket 2026",
            "allow_update": True,
            "expires_in": 2592000,
            "max_scans": None,
            "tags": ["conference", "ticket"],
        }
        payload.update(overrides)
        response = client.post("/api/v1/dynamic-qr", json=payload)
        assert response.status_code == 200
        return response.json()

    def test_create_dynamic_qr(self):
        """Create a dynamic QR code and verify response."""
        data = self._create_dynamic_qr()
        assert data["success"] is True
        assert data["id"].startswith("qr_")
        assert data["short_code"]
        assert "veil.link/r/" in data["redirect_url"]
        assert "/api/v1/dynamic-qr/" in data["qr_image_url"]
        assert "created_at" in data
        assert "expires_at" in data
        assert "request_id" in data

    def test_create_dynamic_qr_no_expiry(self):
        """Create a dynamic QR with no expiration."""
        response = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com/permanent",
                "expires_in": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] is None

    def test_create_dynamic_qr_empty_url(self):
        """Create with empty URL should fail."""
        response = client.post(
            "/api/v1/dynamic-qr",
            json={"destination_url": ""},
        )
        assert response.status_code == 400

    def test_create_dynamic_qr_invalid_url(self):
        """Create with invalid URL should fail."""
        response = client.post(
            "/api/v1/dynamic-qr",
            json={"destination_url": "not-a-url"},
        )
        assert response.status_code == 400

    def test_get_qr_image(self):
        """Generate QR PNG image for a dynamic link."""
        qr = self._create_dynamic_qr()
        response = client.get(f"/api/v1/dynamic-qr/{qr['id']}/qr")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 100

    def test_get_qr_image_not_found(self):
        """Get QR image for non-existent ID should fail."""
        response = client.get("/api/v1/dynamic-qr/nonexistent/qr")
        assert response.status_code == 404

    def test_redirect_endpoint(self):
        """Redirect short_code to destination URL."""
        qr = self._create_dynamic_qr()
        # Follow redirects=False to get 302
        response = client.get(
            f"/api/v1/dynamic-qr/r/{qr['short_code']}",
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/ticket-123"

    def test_redirect_short_code_router(self):
        """Test the /api/v1/r/{short_code} redirect endpoint."""
        qr = self._create_dynamic_qr()
        response = client.get(
            f"/api/v1/r/{qr['short_code']}",
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/ticket-123"

    def test_redirect_not_found(self):
        """Redirect with unknown short_code should fail."""
        response = client.get("/api/v1/r/unknown123", follow_redirects=False)
        assert response.status_code == 404

    def test_redirect_tracks_analytics(self):
        """Redirect should increment scan count and be visible in analytics."""
        qr = self._create_dynamic_qr()

        # Perform multiple scans
        for _ in range(3):
            client.get(
                f"/api/v1/r/{qr['short_code']}",
                headers={"User-Agent": "TestBot/1.0", "Referer": "https://twitter.com"},
                follow_redirects=False,
            )

        # Check analytics
        response = client.get(f"/api/v1/dynamic-qr/{qr['id']}/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 3
        assert data["unique_ips"] >= 1
        assert len(data["scans_over_time"]) >= 1
        assert data["last_scan"] is not None

    def test_analytics_with_bot_agent(self):
        """Verify user agent categorization works."""
        qr = self._create_dynamic_qr()

        client.get(
            f"/api/v1/r/{qr['short_code']}",
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"},
            follow_redirects=False,
        )
        client.get(
            f"/api/v1/r/{qr['short_code']}",
            headers={"User-Agent": "Googlebot/2.1"},
            follow_redirects=False,
        )

        response = client.get(f"/api/v1/dynamic-qr/{qr['id']}/analytics")
        data = response.json()
        agents = {a["agent"] for a in data["top_user_agents"]}
        assert "Mobile" in agents
        assert "Bot" in agents

    def test_update_destination_url(self):
        """Update the destination URL of a dynamic QR."""
        qr = self._create_dynamic_qr()

        response = client.patch(
            f"/api/v1/dynamic-qr/{qr['id']}",
            json={"destination_url": "https://example.com/new-ticket-456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == qr["id"]

        # Verify redirect now goes to new URL
        redirect = client.get(
            f"/api/v1/r/{qr['short_code']}",
            follow_redirects=False,
        )
        assert redirect.headers["location"] == "https://example.com/new-ticket-456"

    def test_update_not_allowed(self):
        """Update should fail if allow_update is False."""
        response = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com/fixed",
                "title": "Fixed QR",
                "allow_update": False,
            },
        )
        qr = response.json()

        response = client.patch(
            f"/api/v1/dynamic-qr/{qr['id']}",
            json={"destination_url": "https://example.com/new"},
        )
        assert response.status_code == 400

    def test_deactivate_qr(self):
        """Deactivate a dynamic QR and verify 410 on redirect."""
        qr = self._create_dynamic_qr()

        response = client.delete(f"/api/v1/dynamic-qr/{qr['id']}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Redirect should now return 410
        redirect = client.get(
            f"/api/v1/r/{qr['short_code']}",
            follow_redirects=False,
        )
        assert redirect.status_code == 410

    def test_list_dynamic_qrs(self):
        """List dynamic QRs with pagination."""
        # Create a few QRs
        for i in range(3):
            client.post(
                "/api/v1/dynamic-qr",
                json={"destination_url": f"https://example.com/item-{i}"},
            )

        response = client.get("/api/v1/dynamic-qr?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["items"], list)
        assert data["total"] >= 3
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_list_dynamic_qrs_filter_active(self):
        """List only active dynamic QRs."""
        response = client.get("/api/v1/dynamic-qr?status=active")
        assert response.status_code == 200

    def test_max_scans_limit(self):
        """QR should stop redirecting after max_scans reached."""
        response = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com/limited",
                "max_scans": 2,
            },
        )
        assert response.status_code == 200
        qr = response.json()

        # First two should work
        for i in range(2):
            r = client.get(
                f"/api/v1/r/{qr['short_code']}",
                follow_redirects=False,
                headers={"User-Agent": f"test-{i}"},
            )
            assert r.status_code == 302, f"Redirect {i+1} should succeed"

        # Third should fail with 410 (max scans reached)
        r = client.get(
            f"/api/v1/r/{qr['short_code']}",
            follow_redirects=False,
            headers={"User-Agent": "test-final"},
        )
        assert r.status_code == 410

    def test_analytics_not_found(self):
        """Analytics for non-existent QR should fail."""
        response = client.get("/api/v1/dynamic-qr/nonexistent/analytics")
        assert response.status_code == 404
