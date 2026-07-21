//! Expiring claim token implementation.

use crate::Error;
use crate::tokens::{TokenClaims, TokenConfig};

/// An expiring claim with one-time-use support.
#[derive(Debug, Clone)]
pub struct ExpiringClaim {
    /// The signed token string.
    pub token: String,
    /// The metadata.
    pub metadata: ExpiringClaimMetadata,
}

/// Metadata for an expiring claim.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ExpiringClaimMetadata {
    /// The resource being claimed.
    pub resource: String,
    /// Expiry timestamp (ISO 8601).
    pub expires_at: String,
    /// Whether this claim can only be used once.
    pub one_time: bool,
    /// Maximum number of uses (None = unlimited within TTL).
    pub max_uses: Option<u32>,
}

impl ExpiringClaim {
    /// Create a new expiring claim.
    ///
    /// This is a convenience wrapper around bearer token generation
    /// that encodes claim-specific metadata in the JWT.
    pub fn new(
        resource: &str,
        one_time: bool,
        max_uses: Option<u32>,
        signing_key: &[u8],
        config: &TokenConfig,
        algorithm: &str,
    ) -> crate::Result<Self> {
        let mut claims = TokenClaims::new(resource)
            .with_ttl(config.default_ttl);

        // Add custom claims for the expiring claim
        let custom_claims = serde_json::json!({
            "resource": resource,
            "one_time": one_time,
            "max_uses": max_uses,
        });

        // We encode the extras in the sub field as a JSON object
        // In the real JWT implementation, these would be custom claims
        let sub = serde_json::json!({
            "resource": resource,
            "one_time": one_time,
        }).to_string();

        claims.sub = sub;

        #[cfg(feature = "jwt")]
        {
            let token = crate::tokens::bearer::jwt_impl::BearerToken::issue(
                claims,
                signing_key,
                config,
                algorithm,
            )?;

            let expires_at = chrono::DateTime::from_timestamp(token.claims.exp as i64, 0)
                .unwrap_or_default()
                .to_rfc3339();

            Ok(Self {
                token: token.raw,
                metadata: ExpiringClaimMetadata {
                    resource: resource.to_string(),
                    expires_at,
                    one_time,
                    max_uses,
                },
            })
        }

        #[cfg(not(feature = "jwt"))]
        {
            // Without JWT feature, create a simpler HMAC-signed token
            let expires_at = (chrono::Utc::now() + chrono::Duration::seconds(config.default_ttl.as_secs() as i64)).to_rfc3339();
            let payload = format!("{}::{}::{}", resource, expires_at, one_time);

            use crate::signing::Signer;
            let key = crate::signing::HmacSha256Key::from_slice(signing_key)
                .map_err(|e| Error::Crypto(e.to_string()))?;
            let sig = key.sign(payload.as_bytes())
                .map_err(|e| Error::Crypto(e.to_string()))?;
            use base64::Engine;
            let token = base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(
                format!("{}:{}", payload, hex::encode(sig)),
            );

            Ok(Self {
                token,
                metadata: ExpiringClaimMetadata {
                    resource: resource.to_string(),
                    expires_at,
                    one_time,
                    max_uses,
                },
            })
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_expiring_claim_creation() {
        let key = b"test_secret_key_for_testing_only_12345";
        let claim = ExpiringClaim::new(
            "resource://tickets/vip-001",
            true,
            None,
            key,
            &TokenConfig::default(),
            "HS256",
        ).unwrap();

        assert_eq!(claim.metadata.resource, "resource://tickets/vip-001");
        assert!(claim.metadata.one_time);
        assert!(!claim.token.is_empty());
        assert!(!claim.metadata.expires_at.is_empty());
    }
}
