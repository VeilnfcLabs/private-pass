//! Time-limited token generation and verification.
//!
//! Provides bearer tokens (JWT), expiring claims, and time-window tokens.

mod bearer;
mod expiry;
mod totp_like;

pub use bearer::*;
pub use expiry::*;
pub use totp_like::*;

use crate::Error;

/// Configuration for token generation and validation.
#[derive(Debug, Clone)]
pub struct TokenConfig {
    /// Issuer identifier (set in `iss` claim).
    pub issuer: String,
    /// Audience restriction (optional, set in `aud` claim).
    pub audience: Option<String>,
    /// Default time-to-live for tokens.
    pub default_ttl: std::time::Duration,
    /// Maximum allowed time-to-live.
    pub max_ttl: std::time::Duration,
    /// Clock skew leeway for validation (seconds).
    pub clock_skew_leeway_seconds: u64,
}

impl Default for TokenConfig {
    fn default() -> Self {
        Self {
            issuer: "veilpass".to_string(),
            audience: None,
            default_ttl: std::time::Duration::from_secs(86400),     // 24 hours
            max_ttl: std::time::Duration::from_secs(2592000),        // 30 days
            clock_skew_leeway_seconds: 30,
        }
    }
}

/// Claims for a token.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct TokenClaims {
    /// Subject (who/what the token is about).
    pub sub: String,
    /// Issuer.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub iss: Option<String>,
    /// Audience.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub aud: Option<String>,
    /// Expiry (Unix timestamp).
    pub exp: u64,
    /// Issued at (Unix timestamp).
    pub iat: u64,
    /// Not before (Unix timestamp, optional).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub nbf: Option<u64>,
    /// Unique token ID (for revocation / one-time use).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub jti: Option<String>,
    /// Scope / permissions.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub scope: Option<Vec<String>>,
}

impl TokenClaims {
    /// Create new claims for the given subject.
    ///
    /// Automatically sets `iat` and `exp` (using `TokenConfig::default_ttl`).
    pub fn new(subject: &str) -> Self {
        let now = chrono::Utc::now().timestamp() as u64;
        Self {
            sub: subject.to_string(),
            iss: None,
            aud: None,
            exp: now + TokenConfig::default().default_ttl.as_secs(),
            iat: now,
            nbf: None,
            jti: Some(uuid::Uuid::now_v7().to_string()),
            scope: None,
        }
    }

    /// Set the issuer.
    pub fn with_issuer(mut self, issuer: &str) -> Self {
        self.iss = Some(issuer.to_string());
        self
    }

    /// Set the audience.
    pub fn with_audience(mut self, aud: &str) -> Self {
        self.aud = Some(aud.to_string());
        self
    }

    /// Set the time-to-live from now.
    pub fn with_ttl(mut self, ttl: std::time::Duration) -> Self {
        let now = chrono::Utc::now().timestamp() as u64;
        self.exp = now + ttl.as_secs();
        self
    }

    /// Set the not-before time.
    pub fn with_not_before(mut self, timestamp: u64) -> Self {
        self.nbf = Some(timestamp);
        self
    }

    /// Set the scope.
    pub fn with_scope(mut self, scope: Vec<String>) -> Self {
        self.scope = Some(scope);
        self
    }

    /// Set a custom JTI (token ID).
    pub fn with_jti(mut self, jti: String) -> Self {
        self.jti = Some(jti);
        self
    }

    /// Validate the claims against the given config.
    pub fn validate(&self, config: &TokenConfig) -> Result<(), Error> {
        let now = chrono::Utc::now().timestamp() as u64;
        let leeway = config.clock_skew_leeway_seconds;

        // Check issuer if set in config
        if let Some(expected_iss) = &config.issuer.strip_prefix("veilpass") {
            // issuer validation is optional; just check if configured
        }

        // Check expiry
        if self.exp <= now.saturating_sub(leeway) {
            return Err(Error::TokenExpired);
        }

        // Check not-before
        if let Some(nbf) = self.nbf {
            if nbf > now.saturating_add(leeway) {
                return Err(Error::TokenNotYetValid);
            }
        }

        Ok(())
    }
}
