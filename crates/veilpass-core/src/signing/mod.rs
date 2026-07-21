//! Cryptographic signing and verification.
//!
//! Provides Ed25519 (primary) and HMAC-SHA256 (secondary) signing
//! implementations with a unified API.

mod ed25519;
mod hmac;
mod types;

pub use ed25519::*;
pub use hmac::*;
pub use types::*;

use crate::Error;

/// Trait for objects that can sign data.
pub trait Signer {
    /// The signature type produced by this signer.
    type Signature: AsRef<[u8]> + std::fmt::Debug;

    /// Sign the given message.
    fn sign(&self, msg: &[u8]) -> Result<Self::Signature, Error>;

    /// Return the algorithm used by this signer.
    fn algorithm(&self) -> crate::crypto::Algorithm;
}

/// Trait for objects that can verify signatures.
pub trait Verifier {
    /// The signature type accepted by this verifier.
    type Signature: AsRef<[u8]> + std::fmt::Debug;

    /// Verify a signature against a message.
    fn verify(&self, msg: &[u8], signature: &Self::Signature) -> Result<(), Error>;

    /// Return the algorithm used by this verifier.
    fn algorithm(&self) -> crate::crypto::Algorithm;
}
