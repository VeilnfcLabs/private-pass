//! Cryptographic utilities for VeilPass.
//!
//! This module provides key generation, secure memory handling, and helpers
//! for the Ed25519 and HMAC-SHA256 cryptographic primitives used throughout.

mod keygen;
mod secure_mem;

pub use keygen::*;
pub use secure_mem::*;

use crate::Error;

/// Supported signing algorithms.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Algorithm {
    /// Ed25519 (Edwards-curve Digital Signature Algorithm) — PRIMARY.
    Ed25519,
    /// HMAC-SHA256 (Hash-based Message Authentication Code) — SECONDARY.
    Hs256,
}

impl Algorithm {
    /// Returns the JWT `alg` string for this algorithm.
    pub fn jwt_alg(&self) -> &'static str {
        match self {
            Algorithm::Ed25519 => "EdDSA",
            Algorithm::Hs256 => "HS256",
        }
    }

    /// Returns the key size in bytes for this algorithm.
    pub fn key_size(&self) -> usize {
        match self {
            Algorithm::Ed25519 => 32, // 256-bit seed
            Algorithm::Hs256 => 32,   // 256-bit symmetric key
        }
    }
}

impl std::fmt::Display for Algorithm {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.jwt_alg())
    }
}
