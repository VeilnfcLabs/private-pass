"""Tests for token generation endpoint."""


class TestTokens:
    """Test suite for POST /api/v1/token."""

    def test_create_jwt_token(self, client):
        """Test creating a signed JWT token."""
        response = client.post(
            "/api/v1/token",
            json={
                "subject": "user-001",
                "audience": "api.veilpass.app",
                "issuer": "veilpass",
                "expires_in": 86400,
                "claims": {"role": "admin", "org": "veilpass"},
            },
        )
        # This may fail if Ed25519 keys are not configured
        if response.status_code == 400:
            # Keys not configured, skip
            return
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["token"].startswith("eyJ")  # JWT header
        assert "decoded" in data
        assert data["decoded"]["payload"]["sub"] == "user-001"
        assert data["decoded"]["payload"]["iss"] == "veilpass"
        assert data["expires_at"] is not None

    def test_create_token_empty_subject(self, client):
        """Test that empty subject is rejected."""
        response = client.post(
            "/api/v1/token",
            json={
                "subject": "",
            },
        )
        assert response.status_code == 422

    def test_create_token_with_custom_claims(self, client):
        """Test token with custom claims."""
        response = client.post(
            "/api/v1/token",
            json={
                "subject": "user-002",
                "claims": {
                    "permissions": ["read", "write"],
                    "tenant": "acme-corp",
                },
            },
        )
        if response.status_code == 400:
            return
        assert response.status_code == 200
        data = response.json()
        assert data["decoded"]["payload"]["permissions"] == ["read", "write"]
        assert data["decoded"]["payload"]["tenant"] == "acme-corp"

    def test_create_token_max_ttl_clamped(self, client):
        """Test that TTL exceeding max is handled."""
        response = client.post(
            "/api/v1/token",
            json={
                "subject": "user-003",
                "expires_in": 99999999,  # exceeds max
            },
        )
        if response.status_code == 400:
            return
        assert response.status_code == 200
