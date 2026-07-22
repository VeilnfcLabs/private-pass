"""Zero-Knowledge Proof authentication endpoints.

Provides Schnorr-based ZK proof generation and verification for
privacy-preserving QR-based credential authentication.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError, NotFoundError
from app.models.schemas import (
    ZKPKeypairResponse,
    ZKPProofRequest,
    ZKPProofResponse,
    ZKPVerifyRequest,
    ZKPVerifyResponse,
    ZKPRegisterKeyRequest,
    ZKPRegisterKeyResponse,
    ZKPRegisteredKeysResponse,
    ZKPRegisteredKeyItem,
)
from app.utils import generate_id, format_timestamp, utcnow
from app.zkp import (
    generate_keypair,
    create_proof,
    verify_proof,
    proof_to_json,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/zkp", tags=["Zero-Knowledge Proof"])

# ── In-memory stores ───────────────────────────────────────────────────────────
# In production these would be replaced with database tables.
_keypair_store: dict[str, dict] = {}  # key_id -> {private_key, public_key, label, created_at}
_registered_keys: dict[str, dict] = {}  # public_key -> {label, created_at, verified}


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "/keypair",
    response_model=ZKPKeypairResponse,
    summary="Generate a new ZKP keypair",
)
async def generate_zkp_keypair(
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate a new Schnorr zero-knowledge proof keypair.

    Returns both the private and public key. The private key must be kept
    secret and used to generate proofs. The public key can be shared and
    registered for later verification.
    """
    private_key, public_key = generate_keypair()
    key_id = generate_id()
    now = format_timestamp(utcnow())

    _keypair_store[key_id] = {
        "id": key_id,
        "private_key": str(private_key),
        "public_key": str(public_key),
        "created_at": now,
    }

    logger.info("zkp_keypair_generated", key_id=key_id)

    return ZKPKeypairResponse(
        key_id=key_id,
        private_key=str(private_key),
        public_key=str(public_key),
        algorithm="schnorr-2048",
        created_at=now,
        request_id=request_id,
    )


@router.post(
    "/proof",
    response_model=ZKPProofResponse,
    summary="Generate a ZK proof for QR authentication",
)
async def generate_proof(
    body: ZKPProofRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Generate a non-interactive Schnorr proof.

    The proof can be serialised to JSON and encoded as a QR code.
    Verifiers can check the proof without learning the private key.
    """
    try:
        private_key = int(body.private_key)
    except ValueError:
        raise InvalidInputError("private_key must be a valid integer")

    if private_key < 1 or private_key >= 2**2048:
        raise InvalidInputError("private_key is out of valid range")

    proof = create_proof(private_key)
    qr_data = proof_to_json(proof)

    logger.info("zkp_proof_generated")

    return ZKPProofResponse(
        proof={
            "t": proof["t"],
            "s": proof["s"],
            "nonce": proof["nonce"],
            "timestamp": proof["timestamp"],
        },
        qr_data=qr_data,
        request_id=request_id,
    )


@router.post(
    "/verify",
    response_model=ZKPVerifyResponse,
    summary="Verify a ZK proof from QR scan",
)
async def verify_zkp_proof(
    body: ZKPVerifyRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Verify a Schnorr zero-knowledge proof.

    The verifier checks:
      - The proof timestamp is fresh (within 5 minutes).
      - The cryptographic equation g^s == t * pk^c (mod p) holds.
    """
    try:
        public_key = int(body.public_key)
    except ValueError:
        raise InvalidInputError("public_key must be a valid integer")

    if public_key < 1 or public_key >= 2**2048:
        raise InvalidInputError("public_key is out of valid range")

    proof_dict = body.proof.model_dump()
    is_valid = verify_proof(proof_dict, public_key)

    logger.info(
        "zkp_proof_verified",
        valid=is_valid,
    )

    return ZKPVerifyResponse(
        valid=is_valid,
        verified_at=format_timestamp(utcnow()),
        proof_fresh=is_valid,
        request_id=request_id,
    )


@router.post(
    "/register-public-key",
    response_model=ZKPRegisterKeyResponse,
    summary="Register a public key for later verification",
)
async def register_public_key(
    body: ZKPRegisterKeyRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Register a ZKP public key with a human-readable label.

    Registered keys can be looked up during verification to map
    a public key to an identity (e.g., a conference badge, device, or user).
    """
    public_key = body.public_key.strip()

    if not public_key:
        raise InvalidInputError("public_key is required")

    if public_key in _registered_keys:
        logger.warning("zkp_public_key_already_registered", public_key=public_key[:16])

    now = format_timestamp(utcnow())
    _registered_keys[public_key] = {
        "public_key": public_key,
        "label": body.label or "Unnamed",
        "created_at": now,
    }

    logger.info("zkp_public_key_registered", label=body.label)

    return ZKPRegisterKeyResponse(
        public_key=public_key,
        label=body.label or "Unnamed",
        registered_at=now,
        request_id=request_id,
    )


@router.get(
    "/registered-keys",
    response_model=ZKPRegisteredKeysResponse,
    summary="List registered public keys",
)
async def list_registered_keys(
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """List all registered ZKP public keys with their labels."""
    keys = [
        ZKPRegisteredKeyItem(
            public_key=data["public_key"],
            label=data["label"],
            registered_at=data["created_at"],
        )
        for data in _registered_keys.values()
    ]

    return ZKPRegisteredKeysResponse(
        keys=keys,
        total=len(keys),
        request_id=request_id,
    )
