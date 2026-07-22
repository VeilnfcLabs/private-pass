"""Tests for post-quantum cryptography endpoints."""

import base64

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPQAlgorithmList:
    """Tests for POST /api/v1/pq/algorithms."""

    def test_list_algorithms(self):
        """Should return the algorithm registry."""
        response = client.post("/api/v1/pq/algorithms")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["algorithms"]) >= 4

        # Check known algorithms
        alg_ids = {a["id"] for a in data["algorithms"]}
        assert "ML-DSA-65" in alg_ids
        assert "ML-DSA-87" in alg_ids
        assert "FN-DSA-512" in alg_ids
        assert "SLH-DSA-128s" in alg_ids

    def test_algorithm_metadata(self):
        """Each algorithm should have complete metadata."""
        response = client.post("/api/v1/pq/algorithms")
        data = response.json()
        for alg in data["algorithms"]:
            assert "id" in alg
            assert "name" in alg
            assert "nist_level" in alg
            assert "signature_size" in alg
            assert "public_key_size" in alg
            assert "status" in alg
            assert "available" in alg


class TestPQSign:
    """Tests for POST /api/v1/pq/sign."""

    def test_sign_requires_liboqs(self):
        """Should return descriptive error since liboqs is not installed."""
        response = client.post(
            "/api/v1/pq/sign",
            json={
                "payload": "test data",
                "algorithm": "ML-DSA-65",
                "private_key": base64.b64encode(b"x" * 64).decode(),
            },
        )
        # Should return 400 because liboqs is not installed
        assert response.status_code == 400
        data = response.json()
        assert "liboqs" in data["error"]["message"].lower() or "not yet available" in data["error"]["message"].lower()

    def test_sign_empty_payload(self):
        """Should reject empty payload (Pydantic validation)."""
        response = client.post(
            "/api/v1/pq/sign",
            json={
                "payload": "",
                "algorithm": "ML-DSA-65",
                "private_key": base64.b64encode(b"x" * 64).decode(),
            },
        )
        # Pydantic min_length=1 on payload → 422
        assert response.status_code in (400, 422)

    def test_sign_invalid_algorithm(self):
        """Should reject unsupported algorithm."""
        response = client.post(
            "/api/v1/pq/sign",
            json={
                "payload": "test",
                "algorithm": "FAKE-ALGO",
                "private_key": base64.b64encode(b"x" * 64).decode(),
            },
        )
        assert response.status_code == 422  # pattern validation

    def test_sign_invalid_base64_key(self):
        """Should reject invalid base64 private key."""
        response = client.post(
            "/api/v1/pq/sign",
            json={
                "payload": "test",
                "algorithm": "ML-DSA-65",
                "private_key": "!!!not-base64!!!",
            },
        )
        assert response.status_code == 400

    def test_sign_too_short_key(self):
        """Should reject implausibly short keys."""
        response = client.post(
            "/api/v1/pq/sign",
            json={
                "payload": "test",
                "algorithm": "ML-DSA-65",
                "private_key": base64.b64encode(b"short").decode(),
            },
        )
        assert response.status_code == 400


class TestPQVerify:
    """Tests for POST /api/v1/pq/verify."""

    def test_verify_requires_liboqs(self):
        """Should return descriptive error since liboqs is not installed."""
        response = client.post(
            "/api/v1/pq/verify",
            json={
                "payload": "test data",
                "signature": base64.b64encode(b"x" * 64).decode(),
                "algorithm": "ML-DSA-65",
                "public_key": base64.b64encode(b"y" * 32).decode(),
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "liboqs" in data["error"]["message"].lower() or "not yet available" in data["error"]["message"].lower()

    def test_verify_empty_payload(self):
        """Should reject empty payload (Pydantic validation)."""
        response = client.post(
            "/api/v1/pq/verify",
            json={
                "payload": "",
                "signature": base64.b64encode(b"x" * 64).decode(),
                "algorithm": "ML-DSA-65",
                "public_key": base64.b64encode(b"y" * 32).decode(),
            },
        )
        # Pydantic min_length=1 on payload → 422
        assert response.status_code in (400, 422)

    def test_verify_invalid_algorithm(self):
        """Should reject unsupported algorithm via validation."""
        response = client.post(
            "/api/v1/pq/verify",
            json={
                "payload": "test",
                "signature": base64.b64encode(b"x" * 64).decode(),
                "algorithm": "BAD-ALGO",
                "public_key": base64.b64encode(b"y" * 32).decode(),
            },
        )
        assert response.status_code == 422

    def test_verify_invalid_base64(self):
        """Should reject invalid base64 in signature or public key."""
        response = client.post(
            "/api/v1/pq/verify",
            json={
                "payload": "test",
                "signature": "!!!bad-base64!!!",
                "algorithm": "ML-DSA-65",
                "public_key": "also-bad!!!",
            },
        )
        assert response.status_code == 400


class TestPQAllAlgorithms:
    """All four algorithms should be recognized."""

    @pytest.mark.parametrize("algorithm", ["ML-DSA-65", "ML-DSA-87", "FN-DSA-512", "SLH-DSA-128s"])
    def test_all_algorithms_listed(self, algorithm):
        """Each algorithm should appear in the list."""
        response = client.post("/api/v1/pq/algorithms")
        alg_ids = {a["id"] for a in response.json()["algorithms"]}
        assert algorithm in alg_ids
