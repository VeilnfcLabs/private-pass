"""Tests for signed link creation endpoint."""


class TestSignedLinks:
    """Test suite for POST /api/v1/signed-link."""

    def test_create_signed_link(self, client):
        """Test creating a basic signed link."""
        response = client.post(
            "/api/v1/signed-link",
            json={
                "resource": "ticket-001",
                "ttl": 86400,
                "one_time": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"].startswith("https://claim.veilpass.app/c/")
        assert len(data["token"]) > 0
        assert len(data["signature"]) > 0
        assert len(data["nonce"]) > 0
        assert data["expires_at"] is not None

    def test_create_signed_link_with_max_uses(self, client):
        """Test signed link with max_uses constraint."""
        response = client.post(
            "/api/v1/signed-link",
            json={
                "resource": "vip-ticket",
                "ttl": 3600,
                "one_time": False,
                "max_uses": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["url"].startswith("https://claim.veilpass.app/c/")

    def test_create_signed_link_zero_ttl(self, client):
        """Test signed link with zero TTL (immediately expires)."""
        response = client.post(
            "/api/v1/signed-link",
            json={
                "resource": "expired-ticket",
                "ttl": 0,
                "one_time": True,
            },
        )
        assert response.status_code == 200

    def test_create_signed_link_empty_resource(self, client):
        """Test that empty resource is rejected."""
        response = client.post(
            "/api/v1/signed-link",
            json={
                "resource": "",
            },
        )
        assert response.status_code == 422

    def test_token_format(self, client):
        """Test that the token has payload.signature format."""
        response = client.post(
            "/api/v1/signed-link",
            json={
                "resource": "test-resource",
                "ttl": 3600,
            },
        )
        data = response.json()
        token = data["token"]
        assert "." in token
        parts = token.split(".")
        assert len(parts) == 2
        assert len(parts[0]) > 0  # payload
        assert len(parts[1]) > 0  # signature
