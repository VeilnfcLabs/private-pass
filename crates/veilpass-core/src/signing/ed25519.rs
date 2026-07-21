//! Ed25519 signing implementation.
//!
//! Ed25519 is the PRIMARY signing algorithm for VeilPass due to its:
//! - Compact signatures (64 bytes)
//! - Fast verification (~6.5 µs with aws-lc-rs)
//! - Deterministic signing (no RNG failures)
//! - Side-channel resistance

use ed25519_dalek::{Signer as _, Verifier as _};
use zeroize::Zeroize;

use crate::Error;
use super::{Signer, Verifier};

/// An Ed25519 signing key.
#[derive(Zeroize)]
#[zeroize(drop)]
pub struct Ed25519SigningKey {
    inner: ed25519_dalek::SigningKey,
}

impl Ed25519SigningKey {
    /// Generate a new random Ed25519 signing key.
    pub fn generate() -> Self {
        let mut rng = rand::thread_rng();
        let inner = ed25519_dalek::SigningKey::generate(&mut rng);
        Self { inner }
    }

    /// Create a signing key from a 32-byte seed.
    pub fn from_seed(seed: &[u8; 32]) -> Self {
        let inner = ed25519_dalek::SigningKey::from_bytes(seed);
        Self { inner }
    }

    /// Create a signing key from a byte slice (must be 32 bytes).
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, Error> {
        let arr: [u8; 32] = bytes.try_into()
            .map_err(|_| Error::InvalidKey("Ed25519 seed must be exactly 32 bytes".into()))?;
        Ok(Self::from_seed(&arr))
    }

    /// Serialize the seed to bytes (for storage).
    pub fn to_bytes(&self) -> [u8; 32] {
        self.inner.to_bytes()
    }

    /// Get the corresponding verification key.
    pub fn verification_key(&self) -> Ed25519VerificationKey {
        Ed25519VerificationKey {
            inner: self.inner.verifying_key(),
        }
    }
}

impl Signer for Ed25519SigningKey {
    type Signature = ed25519_dalek::Signature;

    fn sign(&self, msg: &[u8]) -> Result<Self::Signature, Error> {
        Ok(self.inner.sign(msg))
    }

    fn algorithm(&self) -> crate::crypto::Algorithm {
        crate::crypto::Algorithm::Ed25519
    }
}

/// An Ed25519 verification key (public key).
#[derive(Clone, Debug)]
pub struct Ed25519VerificationKey {
    inner: ed25519_dalek::VerifyingKey,
}

impl Ed25519VerificationKey {
    /// Create a verification key from a 32-byte public key.
    pub fn from_bytes(bytes: &[u8; 32]) -> Result<Self, Error> {
        let inner = ed25519_dalek::VerifyingKey::from_bytes(bytes)
            .map_err(|_| Error::InvalidKey("invalid Ed25519 public key bytes".into()))?;
        Ok(Self { inner })
    }

    /// Create a verification key from a byte slice (must be 32 bytes).
    pub fn from_slice(bytes: &[u8]) -> Result<Self, Error> {
        let arr: [u8; 32] = bytes.try_into()
            .map_err(|_| Error::InvalidKey("Ed25519 public key must be exactly 32 bytes".into()))?;
        Self::from_bytes(&arr)
    }

    /// Serialize the public key to bytes.
    pub fn to_bytes(&self) -> [u8; 32] {
        self.inner.to_bytes()
    }

    /// Compute the key ID (first 8 bytes of SHA-256 of public key, hex-encoded).
    pub fn key_id(&self) -> String {
        use sha2::Digest;
        let hash = sha2::Sha256::digest(self.to_bytes());
        hex::encode(&hash[..8])
    }
}

impl Verifier for Ed25519VerificationKey {
    type Signature = ed25519_dalek::Signature;

    fn verify(&self, msg: &[u8], signature: &Self::Signature) -> Result<(), Error> {
        self.inner.verify(msg, signature)
            .map_err(|_| Error::InvalidSignature)
    }

    fn algorithm(&self) -> crate::crypto::Algorithm {
        crate::crypto::Algorithm::Ed25519
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ed25519_sign_verify() {
        let key = Ed25519SigningKey::generate();
        let msg = b"test message";
        let sig = key.sign(msg).unwrap();
        assert!(key.verification_key().verify(msg, &sig).is_ok());
    }

    #[test]
    fn test_ed25519_tampered_message() {
        let key = Ed25519SigningKey::generate();
        let sig = key.sign(b"original message").unwrap();
        let result = key.verification_key().verify(b"tampered message", &sig);
        assert!(result.is_err());
    }

    #[test]
    fn test_ed25519_wrong_key() {
        let key1 = Ed25519SigningKey::generate();
        let key2 = Ed25519SigningKey::generate();
        let sig = key1.sign(b"message").unwrap();
        let result = key2.verification_key().verify(b"message", &sig);
        assert!(result.is_err());
    }

    #[test]
    fn test_ed25519_from_bytes_roundtrip() {
        let key = Ed25519SigningKey::generate();
        let bytes = key.to_bytes();
        let restored = Ed25519SigningKey::from_bytes(&bytes).unwrap();
        assert_eq!(key.to_bytes(), restored.to_bytes());
    }

    #[test]
    fn test_ed25519_key_id_length() {
        let key = Ed25519SigningKey::generate();
        let kid = key.verification_key().key_id();
        assert_eq!(kid.len(), 16); // 8 bytes = 16 hex chars
    }

    #[test]
    fn test_ed25519_verification_key_idempotent() {
        let key = Ed25519SigningKey::generate();
        let vk = key.verification_key();
        let bytes = vk.to_bytes();
        let restored = Ed25519VerificationKey::from_bytes(&bytes);
        assert_eq!(vk.key_id(), restored.key_id());
    }
}
