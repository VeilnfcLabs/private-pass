"""Post-quantum cryptography API routes for VeilPass.

Provides endpoints to list available PQ algorithms, sign data with a PQ
algorithm, and verify PQ signatures.  Actual PQ operations require native
libraries (liboqs); see :mod:`app.pqc` for details.
"""

from fastapi import APIRouter, Depends
from structlog import get_logger

from app.deps import rate_limit_dependency, request_id_dependency
from app.errors import InvalidInputError
from app.models.schemas import (
    PQAlgorithmItem,
    PQAlgorithmListResponse,
    PQSignRequest,
    PQSignResponse,
    PQVerifyRequest,
    PQVerifyResponse,
)
from app.pqc import get_pq_algorithms, pq_sign, pq_verify

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/pq", tags=["Post-Quantum Cryptography"])


@router.post(
    "/algorithms",
    response_model=PQAlgorithmListResponse,
    summary="List available post-quantum algorithms",
)
async def list_pq_algorithms(
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Return metadata about all supported post-quantum signature algorithms.

    Each entry includes the NIST security level, signature and key sizes,
    FIPS standard status, and whether the algorithm is currently backed by
    a native library.
    """
    algorithms = get_pq_algorithms()
    items = [PQAlgorithmItem(**alg) for alg in algorithms]

    return PQAlgorithmListResponse(
        algorithms=items,
        request_id=request_id,
    )


@router.post(
    "/sign",
    response_model=PQSignResponse,
    summary="Sign data with a post-quantum algorithm",
)
async def sign_with_pq(
    body: PQSignRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Sign *payload* using the specified PQ *algorithm* and *private_key*.

    .. note::

       This endpoint requires ``liboqs`` to be installed.  See
       :mod:`app.pqc` for setup instructions.  Until then, the endpoint
       returns a descriptive error.
    """
    if not body.payload.strip():
        raise InvalidInputError("payload cannot be empty")

    try:
        result = pq_sign(body.payload, body.algorithm, body.private_key)
    except NotImplementedError as exc:
        raise InvalidInputError(str(exc)) from exc

    logger.info(
        "pq_sign_success",
        algorithm=body.algorithm,
    )

    return PQSignResponse(
        signature=result["signature"],
        algorithm=body.algorithm,
        public_key=result["public_key"],
        request_id=request_id,
    )


@router.post(
    "/verify",
    response_model=PQVerifyResponse,
    summary="Verify a post-quantum signature",
)
async def verify_pq_signature(
    body: PQVerifyRequest,
    _: None = Depends(rate_limit_dependency),
    request_id: str = Depends(request_id_dependency),
):
    """Verify a PQ signature against the original payload and public key.

    .. note::

       This endpoint requires ``liboqs`` to be installed.  See
       :mod:`app.pqc` for setup instructions.  Until then, the endpoint
       returns a descriptive error.
    """
    if not body.payload.strip():
        raise InvalidInputError("payload cannot be empty")

    try:
        valid = pq_verify(body.payload, body.signature, body.algorithm, body.public_key)
    except NotImplementedError as exc:
        raise InvalidInputError(str(exc)) from exc

    logger.info(
        "pq_verify_complete",
        algorithm=body.algorithm,
        valid=valid,
    )

    return PQVerifyResponse(
        valid=valid,
        algorithm=body.algorithm,
        request_id=request_id,
    )
