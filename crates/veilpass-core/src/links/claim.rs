//! Claim link generation and verification.
//!
//! A claim link embeds a signed token in a URL:
//! `https://claim.veilpass.app/c/{base64url(token)}`
//!
//! When the `jwt` feature is enabled, tokens are JSON Web Tokens (JWT).
//! Without it, tokens are HMAC-SHA256 signed payload strings.

use std::sync::OnceLock;

use crate::Error;
use crate::tokens::{ExpiringClaim, TokenConfig};

static CLAIM_BASE_URL: OnceLock<String> = OnceLock::new();

fn claim_base_url() -> &str {
    CLAIM_BASE_URL.get().map_or("https://claim.veilpass.app/c", |s| s.as_str())
}

/// Set the base URL for claim links. Called once at startup.
pub fn set_claim_base_url(url: &str) -> Result<(), &str> {
    CLAIM_BASE_URL.set(url.to_string())
}

/// A secure claim link.
#[derive(Debug, Clone)]
pub struct ClaimLink {
    /// The full claim URL.
    pub url: String,
    /// The embedded token (JWT or HMAC-signed payload).
    pub token: String,
    /// Metadata about the claim.
    pub metadata: ClaimMetadata,
}

/// Metadata for a claim link.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ClaimMetadata {
    /// The resource being claimed.
    pub resource: String,
    /// Expiry timestamp (ISO 8601).
    pub expires_at: String,
    /// Whether this claim is one-time-use.
    pub one_time: bool,
    /// When the claim was created.
    pub created_at: String,
}

impl ClaimLink {
    /// Generate a new claim link.
    ///
    /// # Arguments
    /// * `resource` - Identifier for the resource being claimed
    /// * `signing_key` - Signing key bytes
    /// * `config` - Token configuration
    /// * `one_time` - Whether the link can only be used once
    /// * `algorithm` - Signing algorithm ("EdDSA" or "HS256")
    pub fn generate(
        resource: &str,
        signing_key: &[u8],
        config: &TokenConfig,
        one_time: bool,
        algorithm: &str,
    ) -> crate::Result<Self> {
        let claim = ExpiringClaim::new(
            resource,
            one_time,
            None,
            signing_key,
            config,
            algorithm,
        )?;

        let url = format!("{}{}", claim_base_url(), &claim.token);

        Ok(Self {
            url,
            token: claim.token,
            metadata: ClaimMetadata {
                resource: resource.to_string(),
                expires_at: claim.metadata.expires_at,
                one_time,
                created_at: chrono::Utc::now().to_rfc3339(),
            },
        })
    }

    /// Verify a claim link URL and return its metadata.
    ///
    /// # Arguments
    /// * `url` - The full claim link URL to verify
    /// * `verification_key` - Verification key bytes
    /// * `config` - Token configuration
    /// * `algorithm` - Expected signing algorithm
    pub fn verify(
        url: &str,
        verification_key: &[u8],
        config: &TokenConfig,
        algorithm: &str,
    ) -> crate::Result<ClaimMetadata> {
        // Extract the token from the URL
        let token = url
            .strip_prefix(claim_base_url())
            .ok_or_else(|| Error::LinkVerification("invalid claim URL format".into()))?;

        if token.is_empty() {
            return Err(Error::LinkVerification("empty claim token".into()));
        }

        // Verify the token and extract claims
        #[cfg(feature = "jwt")]
        {
            Self::verify_jwt(token, verification_key, config, algorithm)
        }

        #[cfg(not(feature = "jwt"))]
        {
            Self::verify_hmac(token, verification_key, config, algorithm)
        }
    }

    /// JWT-based verification (requires `jwt` feature).
    #[cfg(feature = "jwt")]
    fn verify_jwt(
        token: &str,
        verification_key: &[u8],
        config: &TokenConfig,
        algorithm: &str,
    ) -> crate::Result<ClaimMetadata> {
        let claims = crate::tokens::BearerToken::verify(
            token,
            verification_key,
            config,
            algorithm,
        )?;

        // Parse the resource from the sub claim
        let sub_json: serde_json::Value = serde_json::from_str(&claims.sub)
            .map_err(|_| Error::LinkVerification("invalid claim payload".into()))?;

        let resource = sub_json["resource"]
            .as_str()
            .unwrap_or(&claims.sub)
            .to_string();

        let expires_at = chrono::DateTime::from_timestamp(claims.exp as i64, 0)
            .map(|dt| dt.to_rfc3339())
            .unwrap_or_else(|| chrono::Utc::now().to_rfc3339());

        Ok(ClaimMetadata {
            resource,
            expires_at,
            one_time: sub_json["one_time"].as_bool().unwrap_or(false),
            created_at: chrono::DateTime::from_timestamp(claims.iat as i64, 0)
                .map(|dt| dt.to_rfc3339())
                .unwrap_or_else(|| chrono::Utc::now().to_rfc3339()),
        })
    }

    /// HMAC-based verification (used when `jwt` feature is disabled).
    #[cfg(not(feature = "jwt"))]
    fn verify_hmac(
        token: &str,
        verification_key: &[u8],
        config: &TokenConfig,
        algorithm: &str,
    ) -> crate::Result<ClaimMetadata> {
        use base64::Engine;

        // Decode the base64 token
        let decoded = base64::engine::general_purpose::URL_SAFE_NO_PAD
            .decode(token)
            .map_err(|_| Error::LinkVerification("invalid token encoding".into()))?;

        let decoded_str = String::from_utf8(decoded)
            .map_err(|_| Error::LinkVerification("invalid token format".into()))?;

        // Parse: resource::expires_at::one_time:hex_signature
        let parts: Vec<&str> = decoded_str.splitn(4, ':').collect();
        if parts.len() != 4 {
            return Err(Error::LinkVerification("invalid token structure".into()));
        }

        let resource = parts[0];
        let expires_at = parts[1];
        let one_time_str = parts[2];
        let sig_hex = parts[3];

        // Check expiry
        let expires_at_dt = chrono::DateTime::parse_from_rfc3339(expires_at)
            .map_err(|_| Error::LinkVerification("invalid expiry format".into()))?;
        if expires_at_dt < chrono::Utc::now() {
            return Err(Error::TokenExpired);
        }

        // Verify the signature
        use hex::FromHex;
        let sig_bytes = Vec::<u8>::from_hex(sig_hex)
            .map_err(|_| Error::LinkVerification("invalid signature hex".into()))?;

        match algorithm {
            "EdDSA" | "ed25519" => {
                // For Ed25519, we need to verify with the verification key
                let vk = crate::signing::Ed25519VerificationKey::from_slice(verification_key)
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                let ed_sig = ed25519_dalek::Signature::from_slice(&sig_bytes)
                    .map_err(|_| Error::InvalidSignature)?;
                use crate::signing::Verifier;
                vk.verify(
                    format!("{}::{}::{}", resource, expires_at, one_time_str).as_bytes(),
                    &ed_sig,
                )?;
            }
            "HS256" | "hs256" => {
                let hk = crate::signing::HmacSha256Key::from_slice(verification_key)
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                let mut arr = [0u8; 32];
                if sig_bytes.len() != 32 {
                    return Err(Error::InvalidSignature);
                }
                arr.copy_from_slice(&sig_bytes);
                use crate::signing::Verifier;
                hk.verify(
                    format!("{}::{}::{}", resource, expires_at, one_time_str).as_bytes(),
                    &arr,
                )?;
            }
            _ => {
                return Err(Error::LinkVerification(format!(
                    "unsupported algorithm: {algorithm}"
                )));
            }
        }

        Ok(ClaimMetadata {
            resource: resource.to_string(),
            expires_at: expires_at.to_string(),
            one_time: one_time_str.parse::<bool>().unwrap_or(false),
            created_at: chrono::Utc::now().to_rfc3339(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_claim_link_generate_and_verify() {
        let key = b"test_secret_key_32_bytes_long_for_hmac!";
        let config = TokenConfig::default();

        let link = ClaimLink::generate(
            "resource://tickets/vip-001",
            key,
            &config,
            true,
            "HS256",
        )
        .unwrap();

        assert!(link.url.starts_with("https://claim.veilpass.app/c/"));
        assert_eq!(link.metadata.resource, "resource://tickets/vip-001");
        assert!(link.metadata.one_time);
    }

    #[test]
    fn test_claim_link_metadata_fields() {
        let key = b"test_secret_key_32_bytes_long_for_hmac!";
        let config = TokenConfig::default();

        let link = ClaimLink::generate(
            "resource://files/doc-42",
            key,
            &config,
            false,
            "HS256",
        )
        .unwrap();

        assert_eq!(link.metadata.resource, "resource://files/doc-42");
        assert!(!link.metadata.one_time);
        assert!(!link.metadata.created_at.is_empty());
        assert!(!link.metadata.expires_at.is_empty());
    }
}
