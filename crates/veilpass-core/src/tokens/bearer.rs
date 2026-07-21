//! Bearer token (JWT) implementation.

#[cfg(feature = "jwt")]
mod jwt_impl {
    use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
    use crate::Error;
    use crate::tokens::{TokenClaims, TokenConfig};

    /// A bearer token (JWT) with its metadata.
    #[derive(Debug, Clone)]
    pub struct BearerToken {
        /// The JWT string.
        pub raw: String,
        /// The parsed claims.
        pub claims: TokenClaims,
    }

    impl BearerToken {
        /// Issue a new bearer token.
        ///
        /// # Arguments
        /// * `claims` - The token claims
        /// * `key` - The signing key bytes (Ed25519 private key or HMAC secret)
        /// * `config` - Token configuration
        /// * `algorithm` - JWT algorithm ("EdDSA" or "HS256")
        pub fn issue(
            claims: TokenClaims,
            key: &[u8],
            config: &TokenConfig,
            algorithm: &str,
        ) -> crate::Result<Self> {
            // Validate TTL
            let ttl_secs = claims.exp.saturating_sub(claims.iat);
            if ttl_secs > config.max_ttl.as_secs() {
                return Err(Error::TokenValidation(format!(
                    "TTL of {}s exceeds maximum of {}s",
                    ttl_secs,
                    config.max_ttl.as_secs()
                )));
            }

            let header = Header {
                alg: algorithm.parse()
                    .map_err(|_| Error::TokenValidation(format!("unsupported algorithm: {algorithm}")))?,
                ..Default::default()
            };

            let encoding_key = EncodingKey::from_ed_pem(key)
                .or_else(|_| EncodingKey::from_secret(key));

            let token = encode(&header, &claims, &encoding_key)
                .map_err(|e| Error::TokenValidation(e.to_string()))?;

            Ok(Self { raw: token, claims })
        }

        /// Verify a bearer token and return its claims.
        ///
        /// # Arguments
        /// * `token` - The JWT string to verify
        /// * `key` - The verification key bytes (Ed25519 public key or HMAC secret)
        /// * `config` - Token configuration
        /// * `algorithm` - Expected JWT algorithm (MUST be specified by caller)
        pub fn verify(
            token: &str,
            key: &[u8],
            config: &TokenConfig,
            algorithm: &str,
        ) -> crate::Result<TokenClaims> {
            let mut validation = Validation::new(
                algorithm.parse()
                    .map_err(|_| Error::TokenValidation(format!("unsupported algorithm: {algorithm}")))?,
            );
            validation.leeway = config.clock_skew_leeway_seconds;
            validation.validate_exp = true;
            validation.validate_nbf = true;

            if let Some(aud) = &config.audience {
                validation.set_audience(&[aud]);
            }
            if !config.issuer.is_empty() {
                validation.set_issuer(&[&config.issuer]);
            }

            let decoding_key = DecodingKey::from_ed_pem(key)
                .or_else(|_| DecodingKey::from_secret(key));

            let token_data = decode::<TokenClaims>(token, &decoding_key, &validation)
                .map_err(|e| match e.kind() {
                    jsonwebtoken::errors::ErrorKind::ExpiredSignature => Error::TokenExpired,
                    jsonwebtoken::errors::ErrorKind::InvalidSignature => Error::InvalidSignature,
                    _ => Error::TokenValidation(e.to_string()),
                })?;

            // Additional claims validation
            token_data.claims.validate(config)?;

            Ok(token_data.claims)
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use crate::tokens::TokenClaims;

        #[test]
        fn test_hmac_token_issue_verify() {
            let key = b"test_secret_key_32_bytes_long!!!!!";
            let claims = TokenClaims::new("test-subject")
                .with_issuer("veilpass")
                .with_ttl(std::time::Duration::from_secs(3600));

            let token = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256").unwrap();
            assert!(!token.raw.is_empty());

            let verified = BearerToken::verify(&token.raw, key, &TokenConfig::default(), "HS256").unwrap();
            assert_eq!(verified.sub, "test-subject");
            assert!(verified.exp > verified.iat);
        }

        #[test]
        fn test_expired_token_rejected() {
            let key = b"test_secret_key_32_bytes_long!!!!!";
            let claims = TokenClaims::new("test")
                .with_ttl(std::time::Duration::from_secs(0)); // expired immediately

            let token = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256").unwrap();

            // Small delay to ensure expiry
            std::thread::sleep(std::time::Duration::from_millis(10));

            let result = BearerToken::verify(&token.raw, key, &TokenConfig::default(), "HS256");
            assert!(matches!(result, Err(Error::TokenExpired)));
        }

        #[test]
        fn test_tampered_token_rejected() {
            let key = b"test_secret_key_32_bytes_long!!!!!";
            let claims = TokenClaims::new("test");
            let token = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256").unwrap();

            use base64::Engine;
            // Tamper with the payload (second segment)
            let parts: Vec<&str> = token.raw.split('.').collect();
            let tampered = format!("{}.{}.{}", parts[0], base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(
                br#"{"sub":"hacker"}"#
            ), parts[2]);

            let result = BearerToken::verify(&tampered, key, &TokenConfig::default(), "HS256");
            assert!(matches!(result, Err(Error::InvalidSignature)));
        }

        #[test]
        fn test_token_ttl_exceeds_max() {
            let key = b"test_secret_key_32_bytes_long!!!!!";
            let claims = TokenClaims::new("test")
                .with_ttl(std::time::Duration::from_secs(99999999));
            let result = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256");
            assert!(result.is_err());
        }
    }
}

#[cfg(not(feature = "jwt"))]
mod jwt_stub {
    //! Stub when JWT feature is disabled.
}

// Re-export BearerToken (public API) only when JWT feature is enabled
#[cfg(feature = "jwt")]
pub use jwt_impl::BearerToken;
