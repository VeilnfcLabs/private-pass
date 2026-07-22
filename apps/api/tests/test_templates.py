"""Tests for Template System endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestTemplates:
    """Test template CRUD, rendering, and preview."""

    def _create_template(self, **overrides):
        """Helper: create a template and return the response data."""
        payload = {
            "name": "Conference Ticket 2026",
            "description": "Standard conference ticket with attendee info",
            "type": "signed-link",
            "config": {
                "ttl": 2592000,
                "one_time": True,
                "fields": ["event_name", "attendee_name", "seat", "tier"],
                "required_fields": ["attendee_name"],
                "qr_config": {"format": "png", "ecl": "H", "size": 512},
            },
            "tags": ["conference", "ticket"],
        }
        payload.update(overrides)
        response = client.post("/api/v1/templates", json=payload)
        assert response.status_code == 200
        return response.json()

    def test_create_template(self):
        """Create a credential template."""
        data = self._create_template()
        assert data["success"] is True
        assert data["id"].startswith("tpl_")
        assert data["name"] == "Conference Ticket 2026"
        assert data["type"] == "signed-link"
        assert data["version"] == 1
        assert "created_at" in data
        assert "updated_at" in data
        assert "request_id" in data

    def test_create_template_empty_name(self):
        """Create template with empty name should fail."""
        response = client.post(
            "/api/v1/templates",
            json={
                "name": "",
                "type": "qr",
                "config": {"format": "png"},
            },
        )
        assert response.status_code == 400

    def test_create_template_invalid_type(self):
        """Create template with invalid type should fail."""
        response = client.post(
            "/api/v1/templates",
            json={
                "name": "Bad Template",
                "type": "invalid-type",
                "config": {},
            },
        )
        assert response.status_code == 422  # pydantic validation

    def test_create_template_all_types(self):
        """Create templates of all supported types."""
        for t in ["signed-link", "signed-url", "token", "qr", "nfc"]:
            config = {}
            if t == "signed-link":
                config = {"ttl": 3600}
            elif t == "signed-url":
                config = {"expires_in": 3600}
            elif t == "token":
                config = {"ttl": 86400}
            elif t == "qr":
                config = {"format": "png", "ecl": "H", "size": 512}
            elif t == "nfc":
                config = {"type": "uri", "payload_template": "https://example.com/{uid}"}

            response = client.post(
                "/api/v1/templates",
                json={"name": f"Test {t}", "type": t, "config": config},
            )
            assert response.status_code == 200, f"Failed for type: {t}"
            assert response.json()["type"] == t

    def test_list_templates(self):
        """List all templates with pagination."""
        # Create a template first
        self._create_template()

        response = client.get("/api/v1/templates?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["templates"], list)
        assert data["total"] >= 1
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_list_templates_filter_by_type(self):
        """List templates filtered by type."""
        response = client.get("/api/v1/templates?type=qr")
        assert response.status_code == 200
        data = response.json()
        for tpl in data["templates"]:
            assert tpl["type"] == "qr"

    def test_get_template(self):
        """Get a specific template by ID."""
        created = self._create_template()
        response = client.get(f"/api/v1/templates/{created['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["name"] == created["name"]
        assert data["type"] == "signed-link"

    def test_get_template_not_found(self):
        """Get non-existent template should fail."""
        response = client.get("/api/v1/templates/nonexistent")
        assert response.status_code == 404

    def test_update_template(self):
        """Update a template and verify version increments."""
        created = self._create_template()

        response = client.put(
            f"/api/v1/templates/{created['id']}",
            json={
                "name": "Updated Conference Ticket 2026",
                "description": "Updated description",
                "type": "signed-link",
                "config": {
                    "ttl": 86400,
                    "one_time": False,
                    "fields": ["event_name", "attendee_name"],
                },
                "tags": ["conference", "updated"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Conference Ticket 2026"
        assert data["version"] == 2  # incremented
        assert data["tags"] == ["conference", "updated"]

    def test_update_template_change_type(self):
        """Updating a template to a different type should fail."""
        created = self._create_template()
        response = client.put(
            f"/api/v1/templates/{created['id']}",
            json={
                "name": "Changed Type",
                "type": "qr",
                "config": {"format": "png"},
            },
        )
        assert response.status_code == 400

    def test_delete_template(self):
        """Delete a template."""
        created = self._create_template()
        response = client.delete(f"/api/v1/templates/{created['id']}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify it's gone
        response = client.get(f"/api/v1/templates/{created['id']}")
        assert response.status_code == 404

    def test_delete_template_not_found(self):
        """Delete non-existent template should fail."""
        response = client.delete("/api/v1/templates/nonexistent")
        assert response.status_code == 404

    def test_render_template(self):
        """Render a template with variables."""
        created = self._create_template()
        response = client.post(
            f"/api/v1/templates/{created['id']}/render",
            json={
                "variables": {
                    "event_name": "DevConf 2026",
                    "attendee_name": "John Doe",
                    "seat": "A12",
                    "tier": "vip",
                }
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["id"] == created["id"]
        assert data["type"] == "signed-link"
        assert "rendered" in data

    def test_render_template_not_found(self):
        """Render non-existent template should fail."""
        response = client.post(
            "/api/v1/templates/nonexistent/render",
            json={"variables": {}},
        )
        assert response.status_code == 404

    def test_preview_template(self):
        """Preview a template with example data."""
        created = self._create_template()
        response = client.get(f"/api/v1/templates/{created['id']}/preview")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["id"] == created["id"]
        assert data["name"] == created["name"]
        assert data["type"] == "signed-link"
        assert "preview" in data

    def test_preview_template_not_found(self):
        """Preview non-existent template should fail."""
        response = client.get("/api/v1/templates/nonexistent/preview")
        assert response.status_code == 404

    def test_template_with_builtin_variables(self):
        """Template should support built-in variables {now}, {uuid}, {date}, {time}."""
        response = client.post(
            "/api/v1/templates",
            json={
                "name": "Builtin Vars Test",
                "type": "signed-link",
                "config": {
                    "resource": "user-{uuid}-at-{date}",
                    "ttl": 3600,
                    "one_time": True,
                },
            },
        )
        assert response.status_code == 200
        tpl = response.json()

        render_resp = client.post(
            f"/api/v1/templates/{tpl['id']}/render",
            json={"variables": {}},
        )
        assert render_resp.status_code == 200
        data = render_resp.json()
        rendered_config = data["rendered"].get("rendered_config", {})
        assert "{uuid}" not in rendered_config.get("resource", "")
        assert "{date}" not in rendered_config.get("resource", "")

    def test_template_version_start_at_one(self):
        """New templates should start at version 1."""
        created = self._create_template()
        assert created["version"] == 1
