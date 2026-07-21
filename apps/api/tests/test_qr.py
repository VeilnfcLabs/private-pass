"""Tests for QR code generation endpoint."""

import base64

import pytest


class TestQRGeneration:
    """Test suite for POST /api/v1/qr."""

    def test_generate_png_qr(self, client):
        """Test generating a PNG QR code returns raw image bytes by default."""
        response = client.post(
            "/api/v1/qr",
            json={
                "content": "https://example.com",
                "format": "png",
                "size": 256,
                "ecl": "H",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers.get("X-Request-ID", "")
        assert len(response.content) > 100  # should have actual image data

    def test_generate_svg_qr(self, client):
        """Test generating an SVG QR code."""
        response = client.post(
            "/api/v1/qr",
            json={
                "content": "https://example.com",
                "format": "svg",
                "size": 256,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        body = response.text
        assert "<svg" in body
        assert "</svg>" in body

    def test_generate_qr_with_custom_colors(self, client):
        """Test QR with custom foreground/background colors."""
        response = client.post(
            "/api/v1/qr",
            json={
                "content": "HELLO WORLD",
                "format": "png",
                "color": "#FF0000",
                "bg_color": "#000000",
                "size": 128,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_generate_qr_with_expiration(self, client):
        """Test QR generation with expiration time returns JSON with base64."""
        response = client.post(
            "/api/v1/qr",
            json={
                "content": "https://example.com/secret",
                "format": "png",
                "expires_in": 3600,
            },
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["format"] == "png"
        assert data["encoding"] == "base64"
        assert data["expires_at"] is not None
        # Verify it's valid base64
        base64.b64decode(data["data"])

    def test_generate_qr_empty_content(self, client):
        """Test that empty content returns a validation error."""
        response = client.post(
            "/api/v1/qr",
            json={"content": ""},
        )
        assert response.status_code == 422  # pydantic validation

    def test_generate_qr_invalid_ecl(self, client):
        """Test that invalid ECL level is rejected."""
        response = client.post(
            "/api/v1/qr",
            json={
                "content": "test",
                "ecl": "X",
            },
        )
        assert response.status_code == 422

    def test_generate_qr_content_too_large(self, client):
        """Test QR with content too large for any version (should return error)."""
        large_content = "A" * 5000
        response = client.post(
            "/api/v1/qr",
            json={
                "content": large_content,
                "format": "png",
                "size": 1024,
            },
        )
        # QR code spec limits data size; expect a structured error
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_generate_qr_one_time_flag(self, client):
        """Test that one_time flag is accepted."""
        response = client.post(
            "/api/v1/qr",
            json={
                "content": "https://example.com/claim",
                "one_time": True,
            },
        )
        assert response.status_code == 200
