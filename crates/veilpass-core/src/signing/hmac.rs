//! HMAC-SHA256 signing implementation.
//!
//! HMAC-SHA256 is the SECONDARY signing algorithm, intended for
//! shared-secret scenarios where asymmetric keys are not appropriate.

use hmac::{Hmac, Mac};
use sha2::Sha256;
use zeroize::Zeroize;

use crate::Error;
use super::{Signer, Verifier};

/// An HMAC-SHA256 signing / verification key (symmetric).
#[derive(Zeroize)]
#[zeroize(drop)]
pub struct HmacSha256Key {
    inner: [u8; 32],
}

impl HmacSha256Key {
    /// Generate a new random HMAC-SHA256 key.
    pub fn generate() -> Self {
        let mut bytes = [0u8; 32];
        use rand::RngCore;
        rand::thread_rng().fill_bytes(&mut bytes);
        Self { inner: bytes }
    }

    /// Create a key from a 32-byte array.
    pub fn from_bytes(bytes: &[u8; 32]) -> Self {
        Self { inner: *bytes }
    }

    /// Create a key from a byte slice (must be 32 bytes).
    pub fn from_slice(bytes: &[u8]) -> Result<Self, Error> {
        let arr: [u8; 32] = bytes.try_into()
            .map_err(|_| Error::InvalidKey("HMAC key must be exactly 32 bytes".into()))?;
        Ok(Self::from_bytes(&arr))
    }

    /// Serialize the key to bytes.
    pub fn to_bytes(&self) -> [u8; 32] {
        self.inner
    }

    /// Compute the key ID (first 8 bytes of SHA-256 of key, hex-encoded).
    pub fn key_id(&self) -> String {
        use sha2::Digest;
        let hash = sha2::Sha256::digest(self.inner);
        hex::encode(&hash[..8])
    }
}

impl Signer for HmacSha256Key {
    type Signature = [u8; 32]; // HMAC-SHA256 output is 32 bytes

    fn sign(&self, msg: &[u8]) -> Result<Self::Signature, Error> {
        let mut mac = Hmac::<Sha256>::new_from_slice(&self.inner)
            .map_err(|e| Error::Crypto(e.to_string()))?;
        mac.update(msg);
        let result = mac.finalize();
        Ok(result.into_bytes().into())
    }

    fn algorithm(&self) -> crate::crypto::Algorithm {
        crate::crypto::Algorithm::Hs256
    }
}

impl Verifier for HmacSha256Key {
    type Signature = [u8; 32];

    fn verify(&self, msg: &[u8], signature: &Self::Signature) -> Result<(), Error> {
        let mut mac = Hmac::<Sha256>::new_from_slice(&self.inner)
            .map_err(|e| Error::Crypto(e.to_string()))?;
        mac.update(msg);
        mac.verify_slice(signature)
            .map_err(|_| Error::InvalidSignature)
    }

    fn algorithm(&self) -> crate::crypto::Algorithm {
        crate::crypto::Algorithm::Hs256
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hmac_sign_verify() {
        let key = HmacSha256Key::generate();
        let msg = b"test message";
        let sig = key.sign(msg).unwrap();
        assert!(key.verify(msg, &sig).is_ok());
    }

    #[test]
    fn test_hmac_tampered_message() {
        let key = HmacSha256Key::generate();
        let sig = key.sign(b"original").unwrap();
        let result = key.verify(b"tampered", &sig);
        assert!(result.is_err());
    }

    #[test]
    fn test_hmac_wrong_key() {
        let key1 = HmacSha256Key::generate();
        let key2 = HmacSha256Key::generate();
        let sig = key1.sign(b"message").unwrap();
        let result = key2.verify(b"message", &sig);
        assert!(result.is_err());
    }

    #[test]
    fn test_hmac_key_size() {
        let key = HmacSha256Key::generate();
        assert_eq!(key.to_bytes().len(), 32);
    }

    #[test]
    fn test_hmac_key_id_length() {
        let key = HmacSha256Key::generate();
        assert_eq!(key.key_id().len(), 16);
    }
}
