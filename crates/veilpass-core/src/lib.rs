//! # VeilPass Core
//!
//! Privacy QR + NFC Generator — Core cryptographic and encoding library.
//!
//! ## Feature Flags
//!
//! - `qr`: Enable QR code generation (via `fast_qr`)
//! - `nfc`: Enable NFC NDEF record generation (via `ndef-rs`)
//! - `jwt`: Enable JWT-based token signing (via `jsonwebtoken`)
//! - `wasm`: Enable WASM-compatible randomness
//! - `full`: Enable all features (default)

#![forbid(unsafe_code)]
#![deny(missing_docs, rust_2018_idioms)]
#![allow(unused_crate_dependencies)]
#![cfg_attr(not(test), deny(clippy::unwrap_used, clippy::expect_used))]

pub mod crypto;
pub mod signing;
pub mod tokens;
pub mod links;

#[cfg(feature = "qr")]
pub mod qr;

#[cfg(feature = "nfc")]
pub mod nfc;

/// Unified error type for the core library.
#[derive(Debug, thiserror::Error)]
pub enum Error {
    // — Crypto errors —
    #[error("cryptographic operation failed: {0}")]
    Crypto(String),

    #[error("key not found: {0}")]
    KeyNotFound(String),

    #[error("invalid key: {0}")]
    InvalidKey(String),

    // — Token errors —
    #[error("token expired")]
    TokenExpired,

    #[error("token not yet valid")]
    TokenNotYetValid,

    #[error("invalid token signature")]
    InvalidSignature,

    #[error("token validation failed: {0}")]
    TokenValidation(String),

    // — Link errors —
    #[error("link generation failed: {0}")]
    LinkGeneration(String),

    #[error("link verification failed: {0}")]
    LinkVerification(String),

    // — QR errors —
    #[cfg(feature = "qr")]
    #[error("QR generation failed: {0}")]
    Qr(String),

    // — NFC errors —
    #[cfg(feature = "nfc")]
    #[error("NFC encoding failed: {0}")]
    Nfc(String),

    // — Serialization —
    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    // — IO —
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    // — Internal —
    #[error("internal error: {0}")]
    Internal(String),
}

/// Convenience alias for `Result<T, veilpass_core::Error>`.
pub type Result<T> = std::result::Result<T, Error>;
