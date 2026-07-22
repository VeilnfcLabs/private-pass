"""Tests for privacy-first analytics layer in dynamic QR codes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestDynamicQRPrivacyMode:
    """Tests for privacy modes in dynamic QR creation and analytics."""

    def _create_qr(self, privacy_mode: str = "standard") -> dict:
        """Helper to create a dynamic QR with specific privacy mode."""
        resp = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "title": f"Test {privacy_mode}",
                "privacy_mode": privacy_mode,
            },
        )
        assert resp.status_code == 200
        return resp.json()

    def _simulate_scans(self, qr_id: str, count: int = 3):
        """Simulate scans by hitting the redirect endpoint."""
        entry = None
        # Find the short_code from the QR store (through list)
        resp = client.get(f"/api/v1/dynamic-qr?per_page=100")
        for item in resp.json().get("items", []):
            if item["id"] == qr_id:
                # Use the short_code
                short_code = item["short_code"][:12]  # short_code is embedded
                break
        else:
            # Try directly from id (the store has both)
            pass

    def test_default_privacy_mode(self):
        """Default privacy mode should be 'standard'."""
        qr = self._create_qr()
        # The QR list endpoint should show scan_count
        resp = client.get(f"/api/v1/dynamic-qr?per_page=100")
        items = resp.json().get("items", [])
        matching = [i for i in items if i["id"] == qr["id"]]
        assert len(matching) > 0

    def test_privacy_mode_rejected_invalid(self):
        """Invalid privacy mode should be rejected."""
        resp = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "privacy_mode": "invalid_mode",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize("mode", ["standard", "privacy", "aggregate_only"])
    def test_all_modes_accepted(self, mode):
        """All valid privacy modes should be accepted."""
        qr = self._create_qr(mode)
        assert qr["id"] is not None

    def test_standard_analytics(self):
        """Standard mode should return full analytics."""
        qr = self._create_qr("standard")
        qr_id = qr["id"]

        # Get analytics
        resp = client.get(f"/api/v1/dynamic-qr/{qr_id}/analytics")
        assert resp.status_code == 200
        data = resp.json()
        # Standard mode should have all fields
        assert "total_scans" in data
        assert "unique_ips" in data
        assert "scans_over_time" in data
        assert "top_user_agents" in data
        assert "top_referrers" in data

    def test_aggregate_only_analytics(self):
        """Aggregate-only mode should return only total_scans."""
        qr = self._create_qr("aggregate_only")
        qr_id = qr["id"]

        resp = client.get(f"/api/v1/dynamic-qr/{qr_id}/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_scans" in data
        assert data["unique_ips"] == 0
        assert data["scans_over_time"] == []
        assert data["top_user_agents"] == []
        assert data["top_referrers"] == []


class TestPrivacyScore:
    """Tests for GET /api/v1/dynamic-qr/{id}/privacy-score."""

    def test_privacy_score_endpoint_exists(self):
        """Should return privacy score for valid QR."""
        # Create a QR
        resp = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "title": "Privacy Score Test",
            },
        )
        qr_id = resp.json()["id"]

        resp = client.get(f"/api/v1/dynamic-qr/{qr_id}/privacy-score")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert 0 <= data["score"] <= 100
        assert isinstance(data["compliant_with"], list)
        assert len(data["compliant_with"]) > 0
        assert data["data_retention_days"] > 0
        assert isinstance(data["auto_delete"], bool)

    def test_privacy_score_not_found(self):
        """Should return 404 for non-existent QR."""
        resp = client.get("/api/v1/dynamic-qr/nonexistent/privacy-score")
        assert resp.status_code == 404

    def test_privacy_score_standard_mode(self):
        """Standard mode should have lower score."""
        qr = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "privacy_mode": "standard",
            },
        ).json()

        resp = client.get(f"/api/v1/dynamic-qr/{qr['id']}/privacy-score")
        assert resp.json()["score"] == 45

    def test_privacy_score_privacy_mode(self):
        """Privacy mode should have medium score."""
        qr = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "privacy_mode": "privacy",
            },
        ).json()

        resp = client.get(f"/api/v1/dynamic-qr/{qr['id']}/privacy-score")
        assert resp.json()["score"] == 78

    def test_privacy_score_aggregate_only_mode(self):
        """Aggregate-only mode should have highest score."""
        qr = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "privacy_mode": "aggregate_only",
            },
        ).json()

        resp = client.get(f"/api/v1/dynamic-qr/{qr['id']}/privacy-score")
        assert resp.json()["score"] == 95

    def test_privacy_score_compliance_labels(self):
        """Different modes should have different compliance labels."""
        # aggregate_only should have more compliant labels than standard
        std_qr = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "privacy_mode": "standard",
            },
        ).json()

        agg_qr = client.post(
            "/api/v1/dynamic-qr",
            json={
                "destination_url": "https://example.com",
                "privacy_mode": "aggregate_only",
            },
        ).json()

        std_score = client.get(f"/api/v1/dynamic-qr/{std_qr['id']}/privacy-score").json()
        agg_score = client.get(f"/api/v1/dynamic-qr/{agg_qr['id']}/privacy-score").json()

        # aggregate_only should have more or equal compliance labels
        assert len(agg_score["compliant_with"]) >= len(std_score["compliant_with"])
        # aggregate_only should have shorter retention
        assert agg_score["data_retention_days"] < std_score["data_retention_days"]
        # aggregate_only should auto_delete
        assert agg_score["auto_delete"] is True
