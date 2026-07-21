//! Signed URL generation and verification.
//!
//! A signed URL appends authentication parameters (signature, expiry, key ID)
//! to an existing URL, allowing the holder to access a resource for a limited time.

use crate::Error;

/// A signed URL with expiry and signature.
#[derive(Debug, Clone)]
pub struct SignedUrl {
    /// The full signed URL (base URL + query parameters).
    pub url: String,
    /// The signature parameters.
    pub params: SignedUrlParams,
}

/// Parameters appended to a signed URL.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SignedUrlParams {
    /// Expiry timestamp (Unix timestamp).
    pub expires: u64,
    /// Base64-encoded Ed25519 or HMAC signature.
    pub signature: String,
    /// Key ID (identifies which key signed this URL).
    pub key_id: String,
}

impl SignedUrl {
    /// Sign a URL with the given key.
    ///
    /// The signature covers: HTTP method + URL path + query + expiry timestamp.
    /// This prevents tampering with any part of the URL after signing.
    ///
    /// # Arguments
    /// * `base_url` - The URL to sign (may already contain query parameters)
    /// * `signing_key` - Signing key bytes
    /// * `key_id` - Identifier for the signing key
    /// * `ttl` - Time-to-live for the signed URL
    /// * `algorithm` - Signing algorithm ("EdDSA" or "HS256")
    pub fn sign(
        base_url: &str,
        signing_key: &[u8],
        key_id: &str,
        ttl: std::time::Duration,
        algorithm: &str,
    ) -> crate::Result<Self> {
        let expires = (chrono::Utc::now() + chrono::Duration::seconds(ttl.as_secs() as i64))
            .timestamp() as u64;

        // Build the string to sign (URL path + query + expiry)
        let uri: url::Url = base_url.parse()
            .map_err(|e| Error::LinkGeneration(format!("invalid URL: {e}")))?;

        let path = uri.path();
        let query = uri.query().unwrap_or("");
        let string_to_sign = format!("GET:{}:{}:{}", path, query, expires);

        // Sign with the appropriate algorithm
        let signature = match algorithm {
            "EdDSA" | "ed25519" => {
                use base64::Engine;
                use crate::signing::Signer;
                let sk = crate::signing::Ed25519SigningKey::from_bytes(signing_key)
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                let sig = sk.sign(string_to_sign.as_bytes())
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(
                    sig.to_bytes(),
                )
            }
            "HS256" | "hs256" => {
                use base64::Engine;
                use crate::signing::Signer;
                let hk = crate::signing::HmacSha256Key::from_slice(signing_key)
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                let sig = hk.sign(string_to_sign.as_bytes())
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(
                    sig,
                )
            }
            _ => return Err(Error::LinkGeneration(format!("unsupported algorithm: {algorithm}"))),
        };

        // Append signature parameters to URL
        let separator = if uri.query().is_some() { "&" } else { "?" };
        let signed_url = format!(
            "{}{}expires={}&sig={}&kid={}",
            base_url, separator, expires, signature, key_id
        );

        Ok(Self {
            url: signed_url,
            params: SignedUrlParams {
                expires,
                signature,
                key_id: key_id.to_string(),
            },
        })
    }

    /// Verify a signed URL and return the original URL if valid.
    ///
    /// # Arguments
    /// * `signed_url` - The full signed URL to verify
    /// * `verification_key` - Verification key bytes
    /// * `algorithm` - Expected signing algorithm
    pub fn verify(
        signed_url: &str,
        verification_key: &[u8],
        algorithm: &str,
    ) -> crate::Result<String> {
        let uri: url::Url = signed_url.parse()
            .map_err(|e| Error::LinkVerification(format!("invalid URL: {e}")))?;

        // Extract signature parameters from query
        let expires: u64 = uri.query_pairs()
            .find(|(k, _)| k == "expires")
            .and_then(|(_, v)| v.parse().ok())
            .ok_or_else(|| Error::LinkVerification("missing expires parameter".into()))?;

        let signature = uri.query_pairs()
            .find(|(k, _)| k == "sig")
            .map(|(_, v)| v.to_string())
            .ok_or_else(|| Error::LinkVerification("missing sig parameter".into()))?;

        // Verify expiry
        let now = chrono::Utc::now().timestamp() as u64;
        if expires <= now {
            return Err(Error::TokenExpired);
        }

        // Rebuild the string that was signed
        let path = uri.path();
        let query = uri.query().unwrap_or("");
        // Remove sig, expires, kid from query for verification
        let clean_query: String = uri.query_pairs()
            .filter(|(k, _)| k != "sig" && k != "expires" && k != "kid")
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join("&");

        let string_to_verify = format!("GET:{}:{}:{}", path, clean_query, expires);

        // Verify the signature
        use base64::Engine;
        let sig_bytes = base64::engine::general_purpose::URL_SAFE_NO_PAD.decode(
            &signature,
        )
        .map_err(|_| Error::LinkVerification("invalid signature encoding".into()))?;

        match algorithm {
            "EdDSA" | "ed25519" => {
                use crate::signing::Verifier;
                let vk = crate::signing::Ed25519VerificationKey::from_slice(verification_key)
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                let sig = ed25519_dalek::Signature::from_slice(&sig_bytes)
                    .map_err(|_| Error::InvalidSignature)?;
                vk.verify(string_to_verify.as_bytes(), &sig)?;
            }
            "HS256" | "hs256" => {
                use crate::signing::Verifier;
                let hk = crate::signing::HmacSha256Key::from_slice(verification_key)
                    .map_err(|e| Error::Crypto(e.to_string()))?;
                let mut arr = [0u8; 32];
                if sig_bytes.len() != 32 {
                    return Err(Error::InvalidSignature);
                }
                arr.copy_from_slice(&sig_bytes);
                hk.verify(string_to_verify.as_bytes(), &arr)?;
            }
            _ => return Err(Error::LinkVerification(format!("unsupported algorithm: {algorithm}"))),
        }

        // Reconstruct the original URL (without signature params)
        let base_url = format!(
            "{}://{}{}{}",
            uri.scheme(),
            uri.host_str().unwrap_or(""),
            if let Some(port) = uri.port() { format!(":{port}") } else { String::new() },
            path,
        );
        let original = if clean_query.is_empty() {
            base_url
        } else {
            format!("{}?{}", base_url, clean_query)
        };

        Ok(original)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_signed_url_roundtrip() {
        let key = crate::signing::Ed25519SigningKey::generate();
        let key_bytes = key.to_bytes();
        let vk_bytes = key.verification_key().to_bytes();
        let kid = key.verification_key().key_id();

        let signed = SignedUrl::sign(
            "https://api.example.com/files/secret.pdf",
            &key_bytes,
            &kid,
            std::time::Duration::from_secs(3600),
            "EdDSA",
        ).unwrap();

        assert!(signed.url.contains("expires="));
        assert!(signed.url.contains("sig="));
        assert!(signed.url.contains("kid="));

        let original = SignedUrl::verify(&signed.url, &vk_bytes, "EdDSA").unwrap();
        assert_eq!(original, "https://api.example.com/files/secret.pdf");
    }

    #[test]
    fn test_signed_url_expired() {
        let key = crate::signing::Ed25519SigningKey::generate();
        let key_bytes = key.to_bytes();
        let vk_bytes = key.verification_key().to_bytes();
        let kid = key.verification_key().key_id();

        let signed = SignedUrl::sign(
            "https://api.example.com/files/doc.pdf",
            &key_bytes,
            &kid,
            std::time::Duration::from_secs(0), // expired immediately
            "EdDSA",
        ).unwrap();

        // Small delay
        std::thread::sleep(std::time::Duration::from_millis(10));

        let result = SignedUrl::verify(&signed.url, &vk_bytes, "EdDSA");
        assert!(matches!(result, Err(Error::TokenExpired)));
    }

    #[test]
    fn test_signed_url_tampered() {
        let key = crate::signing::Ed25519SigningKey::generate();
        let key_bytes = key.to_bytes();
        let vk_bytes = key.verification_key().to_bytes();
        let kid = key.verification_key().key_id();

        let signed = SignedUrl::sign(
            "https://api.example.com/files/secret.pdf",
            &key_bytes,
            &kid,
            std::time::Duration::from_secs(3600),
            "EdDSA",
        ).unwrap();

        // Tamper with the URL path
        let tampered = signed.url.replace("secret.pdf", "malicious.exe");
        let result = SignedUrl::verify(&tampered, &vk_bytes, "EdDSA");
        assert!(result.is_err());
    }

    #[test]
    fn test_signed_url_with_query_params() {
        let key = crate::signing::Ed25519SigningKey::generate();
        let key_bytes = key.to_bytes();
        let vk_bytes = key.verification_key().to_bytes();
        let kid = key.verification_key().key_id();

        let signed = SignedUrl::sign(
            "https://api.example.com/search?q=test&page=1",
            &key_bytes,
            &kid,
            std::time::Duration::from_secs(3600),
            "EdDSA",
        ).unwrap();

        let original = SignedUrl::verify(&signed.url, &vk_bytes, "EdDSA").unwrap();
        assert_eq!(original, "https://api.example.com/search?q=test&page=1");
    }
}
