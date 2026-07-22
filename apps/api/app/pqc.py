"""Post-quantum cryptographic algorithm support for credential signing.

Implements a pluggable algorithm interface supporting NIST-standardized
post-quantum signature schemes:

- **ML-DSA (CRYSTALS-Dilithium)** — Primary PQ algorithm, FIPS-205
- **FN-DSA (FALCON)** — Compact signatures for NFC payloads, FIPS-206
- **SLH-DSA (SPHINCS+)** — Conservative security with small public keys, FIPS-205

.. important::

   Actual post-quantum cryptographic operations require native libraries
   such as ``liboqs`` or ``pqcrypto``.  This module provides the interface
   definitions, metadata, and placeholder implementations that raise
   :class:`NotImplementedError` with clear setup instructions.

   When the required native libraries are installed, swap the placeholder
   implementations with real calls to the corresponding PQ API.

Usage::

    from app.pqc import get_pq_algorithms, pq_sign, pq_verify

    algos = get_pq_algorithms()
    # signature = pq_sign(payload, "ML-DSA-65", private_key)
    # valid = pq_verify(payload, signature, "ML-DSA-65", public_key)
"""

import base64
from enum import Enum
from typing import Any

from structlog import get_logger

from app.errors import InvalidInputError

logger = get_logger(__name__)


class PQAlgorithm(str, Enum):
    """Supported post-quantum signature algorithms."""

    ML_DSA_65 = "ML-DSA-65"  # NIST Level 3, ~2.5KB signature
    ML_DSA_87 = "ML-DSA-87"  # NIST Level 5, ~4.6KB signature
    FN_DSA_512 = "FN-DSA-512"  # Compact, ~0.7KB signature
    SLH_DSA_128S = "SLH-DSA-128s"  # Conservative, ~7.9KB signature


# ── Algorithm registry ─────────────────────────────────────────────────────────


_ALGORITHM_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "ML-DSA-65",
        "name": "CRYSTALS-Dilithium",
        "nist_level": 3,
        "signature_size": "~2.5KB",
        "public_key_size": "~1.3KB",
        "status": "FIPS-205 (August 2024)",
        "available": False,
    },
    {
        "id": "ML-DSA-87",
        "name": "CRYSTALS-Dilithium",
        "nist_level": 5,
        "signature_size": "~4.6KB",
        "public_key_size": "~2.5KB",
        "status": "FIPS-205 (August 2024)",
        "available": False,
    },
    {
        "id": "FN-DSA-512",
        "name": "FALCON",
        "nist_level": 1,
        "signature_size": "~0.7KB",
        "public_key_size": "~0.9KB",
        "status": "FIPS-206 (October 2024)",
        "available": False,
    },
    {
        "id": "SLH-DSA-128s",
        "name": "SPHINCS+",
        "nist_level": 1,
        "signature_size": "~7.9KB",
        "public_key_size": "~0.1KB",
        "status": "FIPS-205 (August 2024)",
        "available": False,
    },
]


def get_pq_algorithms() -> list[dict[str, Any]]:
    """Return available post-quantum algorithms with metadata."""
    return list(_ALGORITHM_REGISTRY)


def _require_library() -> None:
    """Raise a clear error telling the caller how to enable PQ crypto.

    This is a placeholder until ``liboqs`` / ``pqcrypto`` bindings are
    installed.  Once available, replace the body of this function with
    a no-op and implement the actual PQ operations below.
    """
    raise NotImplementedError(
        "Post-quantum cryptography requires the 'liboqs' native library "
        "and Python bindings (e.g. 'python-pqc' or 'oqs-python').  "
        "Install with:\n\n"
        "    pip install python-pqc\n\n"
        "Then set VEILPASS_PQ_ENABLED=true in your environment.\n\n"
        "See: https://github.com/open-quantum-safe/liboqs-python"
    )


def pq_sign(payload: str, algorithm: str, private_key_b64: str) -> dict[str, str]:
    """Sign *payload* using the specified PQ *algorithm*.

    Args:
        payload: The message to sign (plain string).
        algorithm: One of the :class:`PQAlgorithm` values.
        private_key_b64: Base64-encoded PQ private key.

    Returns:
        dict with ``signature`` (base64), ``algorithm``, and
        ``public_key`` (base64).

    Raises:
        InvalidInputError: If *algorithm* is unsupported.
        NotImplementedError: If PQ native libraries are not installed.
    """
    # Validate algorithm
    valid_ids = {a["id"] for a in _ALGORITHM_REGISTRY}
    if algorithm not in valid_ids:
        raise InvalidInputError(
            f"Unsupported PQ algorithm '{algorithm}'. "
            f"Supported: {', '.join(sorted(valid_ids))}"
        )

    # Validate private key is plausible
    try:
        key_bytes = base64.b64decode(private_key_b64)
    except Exception as exc:
        raise InvalidInputError(
            f"Invalid base64-encoded private key: {exc}"
        ) from exc

    if len(key_bytes) < 16:
        raise InvalidInputError(
            f"Private key appears too short ({len(key_bytes)} bytes) "
            f"for algorithm '{algorithm}'"
        )

    # ── Placeholder — replace with real PQ call ────────────────────────
    _require_library()

    # When liboqs is available, the implementation would look like:
    #
    #   import oqs
    #   sig = oqs.Signature(algorithm)
    #   sig.secret_key = key_bytes
    #   signature_bytes = sig.sign(payload.encode())
    #   public_key_bytes = sig.generate_keypair()  # or load from separate input
    #
    #   return {
    #       "signature": base64.b64encode(signature_bytes).decode(),
    #       "algorithm": algorithm,
    #       "public_key": base64.b64encode(public_key_bytes).decode(),
    #   }

    # Unreachable — _require_library raises; this return satisfies type checkers
    raise NotImplementedError("PQ signing not yet available")  # pragma: no cover


def pq_verify(payload: str, signature_b64: str, algorithm: str, public_key_b64: str) -> bool:
    """Verify a PQ signature.

    Args:
        payload: The original message that was signed.
        signature_b64: Base64-encoded signature.
        algorithm: One of the :class:`PQAlgorithm` values.
        public_key_b64: Base64-encoded PQ public key.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.

    Raises:
        InvalidInputError: If *algorithm* is unsupported.
        NotImplementedError: If PQ native libraries are not installed.
    """
    valid_ids = {a["id"] for a in _ALGORITHM_REGISTRY}
    if algorithm not in valid_ids:
        raise InvalidInputError(
            f"Unsupported PQ algorithm '{algorithm}'. "
            f"Supported: {', '.join(sorted(valid_ids))}"
        )

    try:
        signature_bytes = base64.b64decode(signature_b64)
        public_key_bytes = base64.b64decode(public_key_b64)
    except Exception as exc:
        raise InvalidInputError(f"Invalid base64 input: {exc}") from exc

    # ── Placeholder — replace with real PQ call ────────────────────────
    _require_library()

    # When liboqs is available:
    #
    #   import oqs
    #   verifier = oqs.Signature(algorithm)
    #   return verifier.verify(payload.encode(), signature_bytes, public_key_bytes)

    raise NotImplementedError("PQ verification not yet available")  # pragma: no cover


def pq_generate_keypair(algorithm: str) -> dict[str, str]:
    """Generate a new PQ keypair for the given *algorithm*.

    Returns:
        dict with ``private_key`` (base64) and ``public_key`` (base64).

    Raises:
        InvalidInputError: If *algorithm* is unsupported.
        NotImplementedError: If PQ native libraries are not installed.
    """
    valid_ids = {a["id"] for a in _ALGORITHM_REGISTRY}
    if algorithm not in valid_ids:
        raise InvalidInputError(
            f"Unsupported PQ algorithm '{algorithm}'. "
            f"Supported: {', '.join(sorted(valid_ids))}"
        )

    _require_library()

    # When liboqs is available:
    #
    #   import oqs
    #   sig = oqs.Signature(algorithm)
    #   public_key = sig.generate_keypair()
    #   private_key = sig.export_secret_key()
    #   return {
    #       "private_key": base64.b64encode(private_key).decode(),
    #       "public_key": base64.b64encode(public_key).decode(),
    #   }

    raise NotImplementedError("PQ key generation not yet available")  # pragma: no cover
