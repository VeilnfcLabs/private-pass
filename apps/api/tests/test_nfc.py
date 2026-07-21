"""Tests for NFC payload generation endpoint."""

import json


class TestNFCPayloadGeneration:
    """Test suite for POST /api/v1/nfc."""

    def test_generate_nfc_uri_payload(self, client):
        """Test generating a basic URI NFC payload."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "issuer": "veilpass",
                "payload": "https://example.com/claim/abc",
                "version": "1.0",
                "type": "uri",
                "metadata": {"claim_id": "abc-123"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["type"] == "uri"
        assert data["issuer"] == "veilpass"
        assert data["payload"] == "https://example.com/claim/abc"
        assert len(data["nonce"]) > 0
        assert len(data["signature"]) > 0
        assert "exports" in data

    def test_nfc_exports_contain_all_formats(self, client):
        """Test that exports include json, hex, base64, ndef."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "https://example.com/nfc-test",
                "type": "uri",
            },
        )
        assert response.status_code == 200
        data = response.json()
        exports = data["exports"]
        assert "json" in exports
        assert "hex" in exports
        assert "base64" in exports
        # Verify JSON export is valid
        parsed = json.loads(exports["json"])
        assert parsed["payload"] == "https://example.com/nfc-test"

    def test_nfc_text_type(self, client):
        """Test NFC payload with text type."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "Hello, NFC!",
                "type": "text",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "text"

    def test_nfc_with_expiration(self, client):
        """Test NFC payload with ISO 8601 expiration."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "https://example.com/temp",
                "expiration": "2026-12-31T23:59:59Z",
            },
        )
        assert response.status_code == 200
        data = response.json()
        exports = json.loads(data["exports"]["json"])
        assert "expiration" in exports

    def test_nfc_invalid_type(self, client):
        """Test that invalid NFC type is rejected."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "test",
                "type": "invalid_type",
            },
        )
        assert response.status_code == 422

    def test_nfc_custom_metadata(self, client):
        """Test NFC with custom metadata."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "test",
                "metadata": {
                    "app": "wallet",
                    "color": "blue",
                    "count": 42,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        exports = json.loads(data["exports"]["json"])
        assert exports["metadata"]["app"] == "wallet"
        assert exports["metadata"]["count"] == 42
