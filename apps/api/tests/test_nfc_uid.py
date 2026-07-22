"""Tests for NFC anti-cloning UID binding feature."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestNFCUidBinding:
    """Tests for UID binding in NFC payload generation."""

    def test_generate_without_uid(self):
        """Default NFC generation should work without UID binding."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "test without uid",
                "type": "text",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "uid" not in data.get("exports", {}) or data["exports"].get("uid") is None

    def test_generate_with_uid_binding(self):
        """Should include UID in payload when bind_to_uid is True."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "uid-bound-credential",
                "type": "uri",
                "bind_to_uid": True,
                "uid": "04:12:34:56:78:9A:BC",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        exports = data["exports"]
        assert "uid" in exports
        assert exports["uid"] == "04:12:34:56:78:9A:BC"
        assert exports["uid_locked"] == "true"
        assert exports["uid_included_in_signature"] == "true"

        # Verify UID is in the signed payload
        payload_doc = json.loads(exports["json"])
        assert payload_doc["uid"] == "04:12:34:56:78:9A:BC"
        assert payload_doc["uid_locked"] is True

    def test_generate_uid_without_bind_flag(self):
        """Providing UID without bind_to_uid should not embed it."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "test",
                "uid": "04:12:34:56:78:9A:BC",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "uid" not in data.get("exports", {})

    def test_bind_uid_without_uid_value(self):
        """bind_to_uid=True without uid should return 400."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "test",
                "bind_to_uid": True,
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "uid is required" in data["error"]["message"].lower()

    def test_bind_uid_with_empty_uid(self):
        """bind_to_uid=True with empty uid should return 400."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "test",
                "bind_to_uid": True,
                "uid": "",
            },
        )
        assert response.status_code == 400

    def test_generate_with_uid_normalizes_case(self):
        """UID should be normalized to uppercase."""
        response = client.post(
            "/api/v1/nfc",
            json={
                "payload": "case-test",
                "bind_to_uid": True,
                "uid": "04:12:34:56:78:9a:bc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Check the raw payload document for normalized UID
        payload_doc = json.loads(data["exports"]["json"])
        assert payload_doc["uid"] == "04:12:34:56:78:9A:BC"


class TestNFCUidVerification:
    """Tests for POST /api/v1/nfc/verify-uid."""

    def test_verify_matching_uid(self):
        """Should confirm UID match when UIDs align."""
        # Generate with UID
        gen = client.post(
            "/api/v1/nfc",
            json={
                "payload": "verify-test",
                "bind_to_uid": True,
                "uid": "04:AB:CD:EF:01:23:45",
            },
        ).json()

        payload_doc = json.loads(gen["exports"]["json"])

        response = client.post(
            "/api/v1/nfc/verify-uid",
            json={
                "payload": payload_doc,
                "uid": "04:AB:CD:EF:01:23:45",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uid_match"] is True
        assert data["uid_in_payload"] is True
        # signature_valid may be False if no signing key is configured

    def test_verify_non_matching_uid(self):
        """Should reject when UIDs don't match."""
        gen = client.post(
            "/api/v1/nfc",
            json={
                "payload": "verify-test",
                "bind_to_uid": True,
                "uid": "04:AA:BB:CC:DD:EE:FF",
            },
        ).json()

        payload_doc = json.loads(gen["exports"]["json"])

        response = client.post(
            "/api/v1/nfc/verify-uid",
            json={
                "payload": payload_doc,
                "uid": "04:11:22:33:44:55:66",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uid_match"] is False
        assert data["uid_in_payload"] is True

    def test_verify_payload_without_uid(self):
        """Should report uid_in_payload=False when no UID present."""
        gen = client.post(
            "/api/v1/nfc",
            json={"payload": "no-uid-test"},
        ).json()

        payload_doc = json.loads(gen["exports"]["json"])

        response = client.post(
            "/api/v1/nfc/verify-uid",
            json={
                "payload": payload_doc,
                "uid": "04:AB:CD:EF:01:23:45",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uid_in_payload"] is False
        assert data["uid_match"] is False

    def test_verify_case_insensitive_uid(self):
        """UID comparison should be case-insensitive."""
        gen = client.post(
            "/api/v1/nfc",
            json={
                "payload": "case-test",
                "bind_to_uid": True,
                "uid": "04:AB:CD:EF:01:23:45",
            },
        ).json()

        payload_doc = json.loads(gen["exports"]["json"])

        # Verify with different case
        response = client.post(
            "/api/v1/nfc/verify-uid",
            json={
                "payload": payload_doc,
                "uid": "04:ab:cd:ef:01:23:45",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uid_match"] is True

    def test_verify_invalid_payload_format(self):
        """Should handle non-dict payload gracefully."""
        response = client.post(
            "/api/v1/nfc/verify-uid",
            json={
                "payload": {"some": "data"},
                "uid": "04:AB:CD:EF:01:23:45",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uid_in_payload"] is False
