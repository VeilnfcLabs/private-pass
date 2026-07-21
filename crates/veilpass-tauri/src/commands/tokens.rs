//! Token generation and verification commands.

use serde::Serialize;
use veilpass_core::tokens::{self, TokenClaims, TokenConfig};
use veilpass_core::signing::Ed25519SigningKey;

use crate::error::{AppError, AppResult, into_app_result};

#[derive(Debug, Serialize)]
pub struct TokenResult {
    pub token: String,
    pub claims: TokenClaimsInfo,
}

#[derive(Debug, Serialize)]
pub struct TokenClaimsInfo {
    pub subject: String,
    pub issuer: String,
    pub issued_at: String,
    pub expires_at: String,
    pub scope: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct TokenVerificationResult {
    pub valid: bool,
    pub claims: Option<TokenClaimsInfo>,
    pub error: Option<String>,
}

/// Issue a new time-limited bearer token.
#[tauri::command]
#[specta::specta]
pub fn issue_token(
    subject: String,
    ttl_secs: Option<u64>,
    scope: Option<Vec<String>>,
    audience: Option<String>,
) -> AppResult<TokenResult> {
    into_app_result(issue_token_inner(&subject, ttl_secs, scope, audience))
}

fn issue_token_inner(
    subject: &str,
    ttl_secs: Option<u64>,
    scope: Option<Vec<String>>,
    audience: Option<String>,
) -> Result<TokenResult, AppError> {
    let config = TokenConfig {
        default_ttl: std::time::Duration::from_secs(ttl_secs.unwrap_or(86400)),
        audience,
        ..Default::default()
    };

    let mut claims = TokenClaims::new(subject)
        .with_ttl(std::time::Duration::from_secs(ttl_secs.unwrap_or(86400)));

    if let Some(s) = scope {
        if !s.is_empty() {
            claims = claims.with_scope(s);
        }
    }

    let key = Ed25519SigningKey::generate();
    let key_bytes = key.to_bytes();

    #[cfg(feature = "jwt")]
    {
        let token = tokens::bearer::jwt_impl::BearerToken::issue(
            claims, &key_bytes, &config, "EdDSA",
        ).map_err(AppError::from)?;

        let scope = token.claims.scope.clone().unwrap_or_default();

        Ok(TokenResult {
            token: token.raw,
            claims: TokenClaimsInfo {
                subject: token.claims.sub.clone(),
                issuer: config.issuer.clone(),
                issued_at: chrono::DateTime::from_timestamp(token.claims.iat as i64, 0)
                    .unwrap_or_default()
                    .to_rfc3339(),
                expires_at: chrono::DateTime::from_timestamp(token.claims.exp as i64, 0)
                    .unwrap_or_default()
                    .to_rfc3339(),
                scope,
            },
        })
    }

    #[cfg(not(feature = "jwt"))]
    {
        Err(AppError::Internal("JWT feature not enabled".to_string()))
    }
}

/// Verify a bearer token.
#[tauri::command]
#[specta::specta]
pub fn verify_token(
    token: String,
) -> TokenVerificationResult {
    // Stub: full verification requires access to the original signing key
    TokenVerificationResult {
        valid: false,
        claims: None,
        error: Some("Verification requires the original signing key (not yet implemented)".to_string()),
    }
}
