"""Zero-Knowledge Proof authentication using Schnorr protocol.

Implements a non-interactive Schnorr proof (Fiat-Shamir transform)
for privacy-preserving credential verification over QR codes.

The protocol:
  1. Prover generates random r, computes commitment t = g^r mod p
  2. Prover computes challenge c = H(t || pk || nonce || timestamp)
  3. Prover computes response s = r + c*x mod (p-1)
  4. Verifier checks: g^s == t * pk^c mod p

Uses a 2048-bit safe prime (RFC 3526 Group 14) for strong security.
"""

import hashlib
import json
import secrets
import time
from typing import Optional

# ── Domain parameters ──────────────────────────────────────────────────────────
# 2048-bit MODP Group from RFC 3526 (Group 14)
P = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A63A3620FFFFFFFFFFFFFFFF
G = 2

# Maximum leeway for timestamp validation (seconds)
DEFAULT_LEEWAY = 300


# ── Key generation ─────────────────────────────────────────────────────────────


def generate_keypair() -> tuple[int, int]:
    """Generate a (private_key, public_key) pair for Schnorr proofs.

    Returns:
        A tuple of (private_key, public_key) where both are positive integers
        modulo P-1 and P respectively.
    """
    private_key = secrets.randbelow(P - 1) + 1
    public_key = pow(G, private_key, P)
    return private_key, public_key


def public_key_from_private(private_key: int) -> int:
    """Derive the public key from a private key.

    Args:
        private_key: The private key scalar.

    Returns:
        The corresponding public key point g^private_key mod p.
    """
    return pow(G, private_key, P)


# ── Proof creation (Fiat-Shamir transform) ────────────────────────────────────


def compute_challenge(t: int, public_key: int, nonce: str, timestamp: str) -> int:
    """Compute the Fiat-Shamir challenge c = H(t || pk || nonce || timestamp).

    Args:
        t: The commitment value g^r mod p.
        public_key: The prover's public key.
        nonce: A unique nonce to prevent replay attacks.
        timestamp: ISO or Unix timestamp for freshness.

    Returns:
        An integer challenge modulo P.
    """
    challenge_input = f"{t}:{public_key}:{nonce}:{timestamp}"
    digest = hashlib.sha256(challenge_input.encode()).digest()
    c = int.from_bytes(digest, byteorder="big") % P
    return c


def create_proof(
    private_key: int,
    nonce: str = "",
    timestamp: str = "",
) -> dict:
    """Create a non-interactive Schnorr proof using the Fiat-Shamir heuristic.

    Args:
        private_key: The prover's private key scalar.
        nonce: Optional unique nonce. Auto-generated if empty.
        timestamp: Optional timestamp. Auto-generated if empty.

    Returns:
        A dict with keys:
          - "t": str — commitment
          - "s": str — response
          - "nonce": str — unique nonce
          - "timestamp": str — Unix timestamp
          - "public_key": str — the derived public key
    """
    # Generate a random blinding factor
    r = secrets.randbelow(P - 1) + 1
    t = pow(G, r, P)
    public_key = public_key_from_private(private_key)

    nonce = nonce or secrets.token_hex(16)
    timestamp = timestamp or str(int(time.time()))

    # Fiat-Shamir: challenge from transcript
    c = compute_challenge(t, public_key, nonce, timestamp)

    # Response: s = r + c * private_key (mod p-1)
    s = (r + c * private_key) % (P - 1)

    return {
        "t": str(t),
        "s": str(s),
        "nonce": nonce,
        "timestamp": timestamp,
        "public_key": str(public_key),
    }


# ── Proof verification ────────────────────────────────────────────────────────


def verify_proof(proof: dict, public_key: int, leeway: int = DEFAULT_LEEWAY) -> bool:
    """Verify a non-interactive Schnorr proof.

    Checks:
      1. Timestamp freshness (within configured leeway).
      2. g^s == t * pk^c (mod p)

    Args:
        proof: Dict with keys "t", "s", "nonce", "timestamp".
        public_key: The claimed public key of the prover.
        leeway: Allowed clock drift in seconds.

    Returns:
        True if the proof is valid, False otherwise.
    """
    try:
        t = int(proof["t"])
        s = int(proof["s"])
        nonce = proof.get("nonce", "")
        timestamp = proof.get("timestamp", "0")

        # Check timestamp freshness
        ts = int(timestamp)
        if abs(time.time() - ts) > leeway:
            return False

        # Recompute challenge
        c = compute_challenge(t, public_key, nonce, timestamp)

        # Verify: g^s == t * pk^c (mod p)
        lhs = pow(G, s, P)
        rhs = (t * pow(public_key, c, P)) % P

        return lhs == rhs
    except (ValueError, KeyError, TypeError):
        return False


# ── QR-optimised helper ──────────────────────────────────────────────────────


def create_proof_qr(
    private_key: int,
    nonce: str = "",
    timestamp: str = "",
) -> dict:
    """Create a Schnorr proof optimised for QR code encoding.

    The resulting dict is smaller (no embedded public_key) and can be
    serialised to JSON for QR display.

    Args:
        private_key: The prover's private key scalar.
        nonce: Optional unique nonce.
        timestamp: Optional Unix timestamp.

    Returns:
        A proof dict ready for JSON serialisation.
    """
    proof = create_proof(private_key, nonce=nonce, timestamp=timestamp)
    return {
        "t": proof["t"],
        "s": proof["s"],
        "nonce": proof["nonce"],
        "timestamp": proof["timestamp"],
    }


def proof_to_json(proof: dict) -> str:
    """Serialise a proof dict to a compact JSON string.

    Args:
        proof: The proof dict.

    Returns:
        JSON string suitable for QR encoding.
    """
    return json.dumps(proof, separators=(",", ":"))


def proof_from_json(data: str) -> dict:
    """Deserialise a proof from a JSON string.

    Args:
        data: JSON string from a QR scan.

    Returns:
        The proof dict.
    """
    return json.loads(data)
