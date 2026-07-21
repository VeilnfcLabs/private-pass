//! Application error types for the Tauri backend.
//!
//! Errors are serialized to a stable tagged shape `{ kind: string, message: string }`
//! for consumption by the frontend.

use serde::Serialize;

/// A serializable application error.
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("crypto error: {0}")]
    Crypto(String),

    #[error("key not found")]
    KeyNotFound,

    #[error("invalid input: {0}")]
    InvalidInput(String),

    #[error("QR generation failed: {0}")]
    QrGeneration(String),

    #[error("NFC generation failed: {0}")]
    NfcGeneration(String),

    #[error("token error: {0}")]
    Token(String),

    #[error("link error: {0}")]
    Link(String),

    #[error("internal error: {0}")]
    Internal(String),
}

/// Serialized error shape for the frontend.
#[derive(Debug, Clone, Serialize)]
pub struct AppErrorResponse {
    pub kind: String,
    pub message: String,
}

impl From<AppError> for AppErrorResponse {
    fn from(err: AppError) -> Self {
        let kind = match &err {
            AppError::Crypto(_) => "crypto",
            AppError::KeyNotFound => "key_not_found",
            AppError::InvalidInput(_) => "invalid_input",
            AppError::QrGeneration(_) => "qr_generation",
            AppError::NfcGeneration(_) => "nfc_generation",
            AppError::Token(_) => "token",
            AppError::Link(_) => "link",
            AppError::Internal(_) => "internal",
        }
        .to_string();

        AppErrorResponse {
            kind,
            message: err.to_string(),
        }
    }
}

impl From<veilpass_core::Error> for AppError {
    fn from(err: veilpass_core::Error) -> Self {
        match err {
            veilpass_core::Error::Crypto(msg) => AppError::Crypto(msg),
            veilpass_core::Error::KeyNotFound(msg) => AppError::Crypto(msg),
            veilpass_core::Error::InvalidKey(msg) => AppError::InvalidInput(msg),
            veilpass_core::Error::TokenExpired => AppError::Token("token expired".into()),
            veilpass_core::Error::TokenNotYetValid => AppError::Token("token not yet valid".into()),
            veilpass_core::Error::InvalidSignature => AppError::Token("invalid signature".into()),
            veilpass_core::Error::TokenValidation(msg) => AppError::Token(msg),
            veilpass_core::Error::LinkGeneration(msg) => AppError::Link(msg),
            veilpass_core::Error::LinkVerification(msg) => AppError::Link(msg),
            veilpass_core::Error::Qr(msg) => AppError::QrGeneration(msg),
            veilpass_core::Error::Nfc(msg) => AppError::NfcGeneration(msg),
            veilpass_core::Error::Keyring(msg) => AppError::Crypto(msg),
            veilpass_core::Error::Serialization(e) => AppError::Internal(e.to_string()),
            veilpass_core::Error::Io(e) => AppError::Internal(e.to_string()),
            veilpass_core::Error::Internal(msg) => AppError::Internal(msg),
        }
    }
}

/// Convenience alias for Tauri command results.
pub type AppResult<T> = Result<T, String>;

/// Convert a `Result<T, AppError>` to `AppResult<T>` (Tauri-compatible).
pub fn into_app_result<T>(result: Result<T, AppError>) -> AppResult<T> {
    match result {
        Ok(val) => Ok(val),
        Err(err) => {
            let resp: AppErrorResponse = err.into();
            Err(serde_json::to_string(&resp).unwrap_or_else(|_| r#"{"kind":"internal","message":"serialization error"}"#.to_string()))
        }
    }
}
