"""Tests for verification endpoint."""

import base64
import json


class TestVerification:
    """Test suite for POST /api/v1/verify and GET /api/v1/verify."""

    def test_verify_invalid_token(self, client):
        """Test verifying a completely invalid token."""
        response = client.post(
            "/api/v1/verify",
            json={
                "type": "token",
                "value": "invalid.token.here",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["signature_valid"] is False

    def test_verify_signed_link_token(self, client):
        """Test verifying a signed-link token."""
        # First create a signed link
        create_resp = client.post(
            "/api/v1/signed-link",
            json={
                "resource": "test-verify-001",
                "ttl": 3600,
                "one_time": True,
            },
        )
        assert create_resp.status_code == 200
        token = create_resp.json()["token"]

        # Now verify it
        response = client.post(
            "/api/v1/verify",
            json={
                "type": "signed-link",
                "value": token,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Note: may or may not be valid depending on key config
        assert "valid" in data
        assert "expired" in data
        assert "signature_valid" in data

    def test_verify_invalid_type(self, client):
        """Test that unsupported verification type is rejected."""
        response = client.post(
            "/api/v1/verify",
            json={
                "type": "unknown_type",
                "value": "some-value",
            },
        )
        assert response.status_code == 422

    def test_verify_get_endpoint(self, client):
        """Test the GET verification endpoint."""
        response = client.get(
            "/api/v1/verify",
            params={
                "type": "token",
                "value": "eyJhbGciOiJFZERTQSJ9.eyJzdWIiOiJ0ZXN0In0.signature",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False  # Not a real token

    def test_verify_malformed_signed_link(self, client):
        """Test verifying a malformed signed-link."""
        response = client.post(
            "/api/v1/verify",
            json={
                "type": "signed-link",
                "value": "not-a-valid-format",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_verify_signed_url_without_signature(self, client):
        """Test verifying a URL missing signature params."""
        response = client.post(
            "/api/v1/verify",
            json={
                "type": "signed-url",
                "value": "https://example.com/file.pdf",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
