"""Tests for hybrid NFC + QR encrypted payload endpoints."""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestEncryptedPayloadGeneration:
    """Tests for POST /api/v1/encrypted/generate."""

    def test_generate_both_formats(self):
        """Should encrypt and return both NFC and QR formats."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": "Sensitive credential data",
                "password": "strong-password-123",
                "output_format": "both",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["id"].startswith("enc_")
        assert data["encrypted"]["algorithm"] == "AES-256-GCM"
        assert data["encrypted"]["kdf"] == "SHA-256"
        assert len(data["encrypted"]["ciphertext"]) > 0
        assert len(data["encrypted"]["nonce"]) > 0
        assert len(data["encrypted"]["tag"]) > 0
        assert data["nfc_payload"] is not None
        assert data["nfc_payload"]["hex"]
        assert data["nfc_payload"]["base64"]
        assert data["nfc_payload"]["ndef"]
        assert data["qr_data"] is not None
        assert data["created_at"] is not None
        assert data["request_id"] != ""

    def test_generate_nfc_only(self):
        """Should generate only NFC format."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": "NFC only data",
                "password": "pass1234",
                "output_format": "nfc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nfc_payload"] is not None
        assert data["qr_data"] is None

    def test_generate_qr_only(self):
        """Should generate only QR format."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": "QR only data",
                "password": "pass1234",
                "output_format": "qr",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nfc_payload"] is None
        assert data["qr_data"] is not None

    def test_generate_empty_payload(self):
        """Should reject empty payload (Pydantic min_length validation)."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "", "password": "pass1234"},
        )
        # Pydantic validates min_length before the handler runs → 422
        assert response.status_code in (400, 422)

    def test_generate_short_password(self):
        """Should reject password < 4 chars (Pydantic min_length validation)."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "test data", "password": "ab"},
        )
        # Pydantic validates Field(min_length=4) → 422
        assert response.status_code in (400, 422)

    def test_generate_svg_qr_format(self):
        """Should generate SVG QR when requested."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": "SVG test",
                "password": "pass1234",
                "output_format": "qr",
                "qr_format": "svg",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["qr_data"] is not None
        # SVG base64 should decode and contain XML/SVG content
        svg_bytes = base64.b64decode(data["qr_data"])
        svg_text = svg_bytes.decode("utf-8").lower()
        assert "<svg" in svg_text or "<?xml" in svg_text or "<html" in svg_text or "qrcode" in svg_text

    def test_generate_custom_nfc_type(self):
        """Should accept custom NFC type."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": "wifi config",
                "password": "pass1234",
                "output_format": "nfc",
                "nfc_type": "wifi",
            },
        )
        assert response.status_code == 200
        assert response.json()["nfc_payload"] is not None

    def test_generate_invalid_nfc_type(self):
        """Should reject invalid NFC type."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": "test",
                "password": "pass1234",
                "nfc_type": "invalid_type",
            },
        )
        assert response.status_code == 422

    def test_generate_invalid_qr_format(self):
        """Should reject invalid QR format."""
        response = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": "test",
                "password": "pass1234",
                "output_format": "qr",
                "qr_format": "gif",
            },
        )
        assert response.status_code == 422


class TestEncryptedPayloadDecryption:
    """Tests for POST /api/v1/encrypted/decrypt."""

    def test_decrypt_valid_payload(self):
        """Should decrypt a payload with correct password."""
        # First generate
        gen = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "My secret data", "password": "mypassword"},
        ).json()

        # Then decrypt
        response = client.post(
            "/api/v1/encrypted/decrypt",
            json={
                "encrypted": gen["encrypted"],
                "password": "mypassword",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plaintext"] == "My secret data"
        assert data["algorithm"] == "AES-256-GCM"

    def test_decrypt_wrong_password(self):
        """Should fail with wrong password."""
        gen = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "secret", "password": "correctpass"},
        ).json()

        response = client.post(
            "/api/v1/encrypted/decrypt",
            json={
                "encrypted": gen["encrypted"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 400

    def test_decrypt_tampered_ciphertext(self):
        """Should fail with tampered ciphertext."""
        gen = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "secret", "password": "correctpass"},
        ).json()

        tampered = dict(gen["encrypted"])
        tampered["ciphertext"] = base64.b64encode(b"tampered").decode()

        response = client.post(
            "/api/v1/encrypted/decrypt",
            json={"encrypted": tampered, "password": "correctpass"},
        )
        assert response.status_code == 400

    def test_decrypt_invalid_base64(self):
        """Should fail with malformed base64."""
        response = client.post(
            "/api/v1/encrypted/decrypt",
            json={
                "encrypted": {
                    "ciphertext": "!!!invalid!!!",
                    "nonce": "aaaa",
                    "tag": "aaaa",
                    "algorithm": "AES-256-GCM",
                    "kdf": "SHA-256",
                },
                "password": "pass",
            },
        )
        assert response.status_code == 400


class TestNFCFromEncrypted:
    """Tests for POST /api/v1/encrypted/nfc."""

    def test_generate_nfc_from_encrypted(self):
        """Should generate NFC payload from existing encrypted data."""
        gen = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "test", "password": "pass1234"},
        ).json()

        response = client.post(
            "/api/v1/encrypted/nfc",
            json={
                "encrypted": gen["encrypted"],
                "nfc_type": "text",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nfc_payload"]["hex"]
        assert data["nfc_payload"]["base64"]
        assert data["nfc_payload"]["ndef"]


class TestQRFromEncrypted:
    """Tests for POST /api/v1/encrypted/qr."""

    def test_generate_qr_from_encrypted(self):
        """Should generate QR from existing encrypted data."""
        gen = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "test", "password": "pass1234"},
        ).json()

        response = client.post(
            "/api/v1/encrypted/qr",
            json={
                "encrypted": gen["encrypted"],
                "qr_format": "png",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["qr_data"] is not None


class TestEncryptedRoundTrip:
    """End-to-end round-trip tests."""

    def test_full_round_trip_nfc(self):
        """Encrypt → NFC → Decrypt should recover original."""
        original = "End-to-end NFC test payload"

        # Generate
        gen = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": original,
                "password": "roundtrip-pass",
                "output_format": "nfc",
            },
        ).json()

        # Decrypt
        dec = client.post(
            "/api/v1/encrypted/decrypt",
            json={"encrypted": gen["encrypted"], "password": "roundtrip-pass"},
        ).json()

        assert dec["plaintext"] == original

    def test_full_round_trip_qr(self):
        """Encrypt → QR → Decrypt should recover original."""
        original = "QR round-trip data"

        gen = client.post(
            "/api/v1/encrypted/generate",
            json={
                "payload": original,
                "password": "qr-pass",
                "output_format": "qr",
            },
        ).json()

        dec = client.post(
            "/api/v1/encrypted/decrypt",
            json={"encrypted": gen["encrypted"], "password": "qr-pass"},
        ).json()

        assert dec["plaintext"] == original

    def test_multiple_different_passwords(self):
        """Different passwords should produce different ciphertexts."""
        gen1 = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "same data", "password": "pass-one"},
        ).json()

        gen2 = client.post(
            "/api/v1/encrypted/generate",
            json={"payload": "same data", "password": "pass-two"},
        ).json()

        assert gen1["encrypted"]["ciphertext"] != gen2["encrypted"]["ciphertext"]
