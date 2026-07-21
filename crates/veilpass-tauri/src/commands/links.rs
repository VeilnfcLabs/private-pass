//! Claim link commands.

use serde::Serialize;
use veilpass_core::links;
use veilpass_core::tokens::TokenConfig;
use veilpass_core::signing::Ed25519SigningKey;

use crate::state::AppState;
use crate::error::{AppError, AppResult, into_app_result};

#[derive(Debug, Serialize)]
pub struct ClaimLinkResult {
    pub url: String,
    pub metadata: ClaimLinkMetadata,
}

#[derive(Debug, Serialize)]
pub struct ClaimLinkMetadata {
    pub resource: String,
    pub expires_at: String,
    pub one_time: bool,
}

#[derive(Debug, Serialize)]
pub struct LinkVerificationResult {
    pub valid: bool,
    pub metadata: Option<ClaimLinkMetadata>,
    pub error: Option<String>,
}

/// Create a new secure claim link.
#[tauri::command]
#[specta::specta]
pub fn create_claim_link(
    _state: tauri::State<'_, AppState>,
    resource: String,
    ttl_secs: Option<u64>,
    one_time: Option<bool>,
) -> AppResult<ClaimLinkResult> {
    into_app_result(create_claim_link_inner(_state, &resource, ttl_secs, one_time))
}

fn create_claim_link_inner(
    _state: tauri::State<'_, AppState>,
    resource: &str,
    ttl_secs: Option<u64>,
    one_time: Option<bool>,
) -> Result<ClaimLinkResult, AppError> {
    let config = TokenConfig {
        default_ttl: std::time::Duration::from_secs(ttl_secs.unwrap_or(86400)),
        ..Default::default()
    };

    let key = Ed25519SigningKey::generate();
    let key_bytes = key.to_bytes();

    let link = links::ClaimLink::generate(
        resource,
        &key_bytes,
        &config,
        one_time.unwrap_or(true),
        "EdDSA",
    ).map_err(AppError::from)?;

    Ok(ClaimLinkResult {
        url: link.url,
        metadata: ClaimLinkMetadata {
            resource: link.metadata.resource,
            expires_at: link.metadata.expires_at,
            one_time: link.metadata.one_time,
        },
    })
}

/// Verify a claim link URL.
#[tauri::command]
#[specta::specta]
pub fn verify_claim_link(
    _state: tauri::State<'_, AppState>,
    url: String,
) -> LinkVerificationResult {
    // For now, return a stub (full verification requires the signing key)
    LinkVerificationResult {
        valid: false,
        metadata: None,
        error: Some("Verification requires the original signing key".to_string()),
    }
}
