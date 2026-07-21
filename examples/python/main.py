"""
VeilPass API — Python example

Demonstrates all 6 API operations using httpx with proper error handling.
Run: pip install httpx && python main.py
"""

import os
import sys
from typing import Any

import httpx

# ── Configuration ──────────────────────────────────────────────────────────────

API_BASE = os.environ.get("VEILPASS_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("VEILPASS_API_KEY", "")

HEADERS = {"Content-Type": "application/json"}
if API_KEY:
    HEADERS["X-API-Key"] = API_KEY


def log(label: str, data: dict[str, Any]) -> None:
    print(f"\n── {label} ──")
    print(__import__("json").dumps(data, indent=2))


# ── 1. QR Generation ────────────────────────────────────────────────────────────

def generate_qr(client) -> dict:
    res = client.post(
        "/api/v1/qr",
        json={
            "content": "https://veilpass.app",
            "format": "png",
            "ecl": "H",
            "size": 512,
            "margin": 4,
            "color": "#000000",
            "bg_color": "#FFFFFF",
            "include_logo": False,
            "one_time": False,
            "expires_in": None,
        },
        headers={"Accept": "application/json"},
    )
    res.raise_for_status()
    data = res.json()
    log("QR Generation", data)
    return data


# ── 2. NFC Payload ──────────────────────────────────────────────────────────────

def generate_nfc(client) -> dict:
    res = client.post(
        "/api/v1/nfc",
        json={
            "issuer": "veilpass",
            "payload": "https://veilpass.app/contact",
            "version": "1.0",
            "type": "uri",
            "expiration": None,
            "metadata": {"department": "engineering"},
        },
    )
    res.raise_for_status()
    data = res.json()
    log("NFC Payload", data)
    return data


# ── 3. Signed Link ─────────────────────────────────────────────────────────────

def create_signed_link(client) -> dict:
    res = client.post(
        "/api/v1/signed-link",
        json={
            "resource": "documents/nda-q3-2026.pdf",
            "ttl": 86400,
            "one_time": True,
            "max_uses": 5,
        },
    )
    res.raise_for_status()
    data = res.json()
    log("Signed Link", data)
    return data


# ── 4. Signed URL ──────────────────────────────────────────────────────────────

def create_signed_url(client) -> dict:
    res = client.post(
        "/api/v1/signed-url",
        json={
            "url": "https://storage.veilpass.app/reports/audit.pdf",
            "permissions": "read",
            "expires_in": 3600,
            "download_limit": 10,
            "one_time": False,
        },
    )
    res.raise_for_status()
    data = res.json()
    log("Signed URL", data)
    return data


# ── 5. Token Generation ────────────────────────────────────────────────────────

def generate_token(client) -> dict:
    res = client.post(
        "/api/v1/token",
        json={
            "subject": "user_abc123",
            "audience": "api.veilpass.app",
            "issuer": "veilpass",
            "expires_in": 86400,
            "claims": {"role": "admin", "region": "us-east"},
        },
    )
    res.raise_for_status()
    data = res.json()
    log("Token", data)
    return data


# ── 6. Verification ─────────────────────────────────────────────────────────────

def verify(client, type_: str, value: str) -> dict:
    res = client.post(
        "/api/v1/verify",
        json={"type": type_, "value": value},
    )
    res.raise_for_status()
    data = res.json()
    log("Verification", data)
    return data


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    with httpx.Client(base_url=API_BASE, headers=HEADERS, timeout=30) as client:
        qr = generate_qr(client)
        assert qr["success"], "QR generation failed"

        nfc = generate_nfc(client)
        assert nfc["success"], "NFC generation failed"

        link = create_signed_link(client)
        assert link["success"], "Signed link creation failed"

        signed_url = create_signed_url(client)
        assert signed_url["success"], "Signed URL creation failed"

        token = generate_token(client)
        assert token["success"], "Token generation failed"

        verification = verify(client, "token", token["token"])
        assert verification["valid"], "Token verification failed"

    print("\n✅ All API operations completed successfully.")


if __name__ == "__main__":
    main()
