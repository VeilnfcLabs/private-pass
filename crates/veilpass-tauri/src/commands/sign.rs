//! URL signing commands.

use serde::Serialize;
use veilpass_core::links;
use veilpass_core::signing::Ed25519SigningKey;

use crate::error::{AppError, AppResult, into_app_result};

#[derive(Debug, Serialize)]
pub struct SignedUrlResult {
    pub url: String,
    pub expires_at: u64,
    pub key_id: String,
}

/// Sign a URL with an expiry timestamp.
#[tauri::command]
#[specta::specta]
pub fn sign_url(
    url: String,
    ttl_secs: Option<u64>,
) -> AppResult<SignedUrlResult> {
    into_app_result(sign_url_inner(&url, ttl_secs))
}

fn sign_url_inner(
    url: &str,
    ttl_secs: Option<u64>,
) -> Result<SignedUrlResult, AppError> {
    let key = Ed25519SigningKey::generate();
    let key_bytes = key.to_bytes();
    let kid = key.verification_key().key_id();

    let signed = links::SignedUrl::sign(
        url,
        &key_bytes,
        &kid,
        std::time::Duration::from_secs(ttl_secs.unwrap_or(3600)),
        "EdDSA",
    ).map_err(AppError::from)?;

    Ok(SignedUrlResult {
        url: signed.url,
        expires_at: signed.params.expires,
        key_id: signed.params.key_id,
    })
}
