"""Selective Disclosure JWT (SD-JWT) support for VeilPass.

Implements salted claim hashes and selective disclosure per
draft-ietf-oauth-selective-disclosure-jwt.

Each disclosable claim gets a random salt, the disclosure blob
[salt, key, value] is base64-encoded, its SHA-256 digest is embedded
in the JWT payload as _sd_{key}. The holder later reveals only the
disclosures (and thus claims) they choose.
"""

import base64
import hashlib
import json
import secrets
import time
from typing import Any

from app.crypto import create_jwt, decode_jwt


def _salt() -> str:
    """Generate a cryptographically random 128-bit salt (hex)."""
    return secrets.token_hex(16)


def create_sd_jwt(
    claims: dict[str, Any],
    ttl: int,
    issuer: str,
    audience: str,
    disclosable_claims: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Create an SD-JWT.

    Args:
        claims: Full set of claims (both plain and disclosable).
        ttl: Lifetime in seconds.
        issuer: JWT issuer.
        audience: JWT audience.
        disclosable_claims: Which claim keys get SD treatment.
            ``None`` (default) means every claim is disclosable.
            An empty list means no claim is disclosable (all go directly
            into the JWT payload).

    Returns:
        (sd_jwt_string, disclosures) where disclosures is a list of
        base64url-encoded disclosure strings (one per disclosable claim).
    """
    if disclosable_claims is None:
        disclosable_claims = list(claims.keys())

    disclosures: list[str] = []
    sd_digests: dict[str, str] = {}
    direct_claims: dict[str, Any] = {}

    for key, value in claims.items():
        if key in disclosable_claims:
            # — Selective-disclosure claim: digest goes in JWT, disclosure returned separately —
            salt = _salt()
            disclosure = json.dumps([salt, key, value], separators=(",", ":"))
            disclosure_b64 = (
                base64.urlsafe_b64encode(disclosure.encode())
                .decode()
                .rstrip("=")
            )
            disclosures.append(disclosure_b64)

            digest = hashlib.sha256(disclosure.encode()).digest()
            sd_digests[f"_sd_{key}"] = (
                base64.urlsafe_b64encode(digest).decode().rstrip("=")
            )
        else:
            # — Plain claim embedded directly —
            direct_claims[key] = value

    # Assemble the JWT payload
    now = int(time.time())
    sd_payload = {
        **direct_claims,
        **sd_digests,
        "iss": issuer,
        "iat": now,
        "exp": now + ttl,
        "_sd_alg": "sha-256",
    }
    if audience:
        sd_payload["aud"] = audience

    token = create_jwt(sd_payload, ttl, issuer, audience)

    return token, disclosures


def verify_sd_jwt(
    token: str,
    disclosures: list[str],
    audience: str = "",
) -> dict[str, Any]:
    """Verify an SD-JWT and return **only** the disclosed claims.

    Args:
        token: The SD-JWT string.
        disclosures: List of base64url-encoded disclosure strings
            the holder chose to reveal.
        audience: Expected JWT audience.  If empty the claim is not verified.

    Returns:
        A dict of verified disclosed claims.

    Raises:
        ValueError: If a disclosure digest does not match the JWT payload.
        jwt.ExpiredSignatureError: If the JWT has expired.
        jwt.InvalidTokenError: If the JWT is malformed or signature invalid.
    """
    payload = decode_jwt(token, audience=audience)

    disclosed: dict[str, Any] = {}

    for disclosure_b64 in disclosures:
        # Restore padding
        padded = disclosure_b64 + "=" * ((4 - len(disclosure_b64) % 4) % 4)
        try:
            disclosure = json.loads(base64.urlsafe_b64decode(padded))
        except Exception as exc:
            raise ValueError(f"Invalid disclosure encoding: {exc}") from exc

        if not isinstance(disclosure, list) or len(disclosure) != 3:
            raise ValueError("Invalid disclosure structure — expected [salt, key, value]")

        _salt, key, value = disclosure

        # Recompute the digest
        reencoded = json.dumps(disclosure, separators=(",", ":")).encode()
        expected_digest_b64 = (
            base64.urlsafe_b64encode(hashlib.sha256(reencoded).digest())
            .decode()
            .rstrip("=")
        )

        stored_digest_b64 = payload.get(f"_sd_{key}")
        if stored_digest_b64 is None:
            raise ValueError(
                f"No SD digest found for claim '{key}' in the JWT payload"
            )

        if stored_digest_b64 != expected_digest_b64:
            raise ValueError(
                f"Disclosure digest mismatch for claim: '{key}'"
            )

        disclosed[key] = value

    return disclosed


def present_sd_jwt(
    disclosures: list[str],
    reveal_claims: list[str],
) -> list[str]:
    """Filter a disclosure list to only the claims the holder wants to reveal.

    Args:
        disclosures: All disclosures previously returned by *create_sd_jwt*.
        reveal_claims: Subset of claim keys to disclose.

    Returns:
        Filtered list of base64url-encoded disclosure strings.
    """
    reveal_set = set(reveal_claims)
    filtered: list[str] = []

    for disclosure_b64 in disclosures:
        padded = disclosure_b64 + "=" * ((4 - len(disclosure_b64) % 4) % 4)
        try:
            disclosure = json.loads(base64.urlsafe_b64decode(padded))
        except Exception:
            # Skip malformed disclosures silently
            continue

        if isinstance(disclosure, list) and len(disclosure) == 3:
            if disclosure[1] in reveal_set:
                filtered.append(disclosure_b64)

    return filtered
