//! Types for the signing module.

use crate::crypto::Algorithm;

/// A digital signature with its metadata.
#[derive(Debug, Clone)]
pub struct Signature {
    /// The raw signature bytes.
    pub bytes: Vec<u8>,
    /// The algorithm used to produce this signature.
    pub algorithm: Algorithm,
}

impl Signature {
    /// Create a new signature.
    pub fn new(bytes: Vec<u8>, algorithm: Algorithm) -> Self {
        Self { bytes, algorithm }
    }
}

impl AsRef<[u8]> for Signature {
    fn as_ref(&self) -> &[u8] {
        &self.bytes
    }
}

/// A unified signing key that can wrap either an Ed25519 or HMAC key.
#[derive(Debug)]
pub enum SigningKey {
    /// Ed25519 signing key.
    Ed25519(super::Ed25519SigningKey),
    /// HMAC-SHA256 signing key.
    Hmac(super::HmacSha256Key),
}

impl SigningKey {
    /// Sign the given message.
    pub fn sign(&self, msg: &[u8]) -> crate::Result<Signature> {
        match self {
            Self::Ed25519(k) => {
                let sig = k.sign(msg)?;
                Ok(Signature::new(sig.to_bytes().to_vec(), Algorithm::Ed25519))
            }
            Self::Hmac(k) => {
                let sig = k.sign(msg)?;
                Ok(Signature::new(sig.to_vec(), Algorithm::Hs256))
            }
        }
    }

    /// Get the verification key (for Ed25519) or a clone (for HMAC).
    pub fn verifier(&self) -> VerificationKey {
        match self {
            Self::Ed25519(k) => VerificationKey::Ed25519(k.verification_key()),
            Self::Hmac(k) => VerificationKey::Hmac(k.clone()),
        }
    }

    /// Get the algorithm.
    pub fn algorithm(&self) -> Algorithm {
        match self {
            Self::Ed25519(_) => Algorithm::Ed25519,
            Self::Hmac(_) => Algorithm::Hs256,
        }
    }
}

/// A unified verification key.
#[derive(Clone, Debug)]
pub enum VerificationKey {
    /// Ed25519 verification key.
    Ed25519(super::Ed25519VerificationKey),
    /// HMAC-SHA256 key (symmetric).
    Hmac(super::HmacSha256Key),
}

impl VerificationKey {
    /// Verify a signature against a message.
    pub fn verify(&self, msg: &[u8], signature: &Signature) -> crate::Result<()> {
        match (self, signature.algorithm) {
            (Self::Ed25519(vk), Algorithm::Ed25519) => {
                let sig = ed25519_dalek::Signature::from_slice(&signature.bytes)
                    .map_err(|_| crate::Error::InvalidSignature)?;
                vk.verify(msg, &sig)
            }
            (Self::Hmac(k), Algorithm::Hs256) => {
                let sig: [u8; 32] = signature.bytes.as_slice().try_into()
                    .map_err(|_| crate::Error::InvalidSignature)?;
                k.verify(msg, &sig)
            }
            _ => Err(crate::Error::Crypto(
                "algorithm mismatch between key and signature".into()
            )),
        }
    }

    /// Get the algorithm.
    pub fn algorithm(&self) -> Algorithm {
        match self {
            Self::Ed25519(_) => Algorithm::Ed25519,
            Self::Hmac(_) => Algorithm::Hs256,
        }
    }

    /// Get the key ID (first 8 bytes of SHA-256 hash, hex-encoded).
    pub fn key_id(&self) -> String {
        match self {
            Self::Ed25519(vk) => vk.key_id(),
            Self::Hmac(k) => k.key_id(),
        }
    }
}
