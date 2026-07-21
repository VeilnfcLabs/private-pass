//! Integration tests for token issue, verify, expiry, and tamper detection.

use veilpass_core::tokens::{BearerToken, TokenClaims, TokenConfig, TimeWindowToken};

/// Test basic JWT issue and verify with HMAC-SHA256.
#[test]
fn test_jwt_hmac_issue_verify() {
    let key = b"test_hmac_secret_key_32_byte_long!!";
    let claims = TokenClaims::new("user-42")
        .with_issuer("veilpass")
        .with_ttl(std::time::Duration::from_secs(3600));

    let token = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256")
        .expect("should issue token");
    assert!(!token.raw.is_empty(), "token should not be empty");

    let verified = BearerToken::verify(&token.raw, key, &TokenConfig::default(), "HS256")
        .expect("should verify token");
    assert_eq!(verified.sub, "user-42", "subject should match");
    assert_eq!(
        verified.iss.as_deref(),
        Some("veilpass"),
        "issuer should match"
    );
}

/// Test that an expired token is rejected.
#[test]
fn test_expired_token_rejected() {
    let key = b"test_hmac_secret_key_32_byte_long!!";
    let claims = TokenClaims::new("temp-user")
        .with_ttl(std::time::Duration::from_secs(0)); // expires immediately

    let token = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256")
        .expect("should issue token");

    // Small delay to ensure expiry
    std::thread::sleep(std::time::Duration::from_millis(50));

    let result = BearerToken::verify(&token.raw, key, &TokenConfig::default(), "HS256");
    assert!(
        result.is_err(),
        "expired token should be rejected: {:?}",
        result
    );
}

/// Test that a tampered token (modified payload) is rejected.
#[test]
fn test_tampered_token_rejected() {
    use base64::Engine;

    let key = b"test_hmac_secret_key_32_byte_long!!";
    let claims = TokenClaims::new("user-42")
        .with_ttl(std::time::Duration::from_secs(3600));

    let token = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256")
        .expect("should issue token");

    // Tamper with the payload segment (second segment of JWT)
    let parts: Vec<&str> = token.raw.split('.').collect();
    assert_eq!(parts.len(), 3, "JWT should have 3 parts");

    let tampered_payload = base64::engine::general_purpose::URL_SAFE_NO_PAD
        .encode(br#"{"sub":"hacker","exp":9999999999}"#);
    let tampered = format!("{}.{}.{}", parts[0], tampered_payload, parts[2]);

    let result = BearerToken::verify(&tampered, key, &TokenConfig::default(), "HS256");
    assert!(
        result.is_err(),
        "tampered token should be rejected: {:?}",
        result
    );
}

/// Test that a token signed with a different key is rejected.
#[test]
fn test_wrong_key_rejected() {
    let key1 = b"first_secret_key_32_bytes_long_abcd";
    let key2 = b"second_secret_key_32_bytes_long_efgh";

    let claims = TokenClaims::new("user-42")
        .with_ttl(std::time::Duration::from_secs(3600));

    let token = BearerToken::issue(claims, key1, &TokenConfig::default(), "HS256")
        .expect("should issue token");

    let result = BearerToken::verify(&token.raw, key2, &TokenConfig::default(), "HS256");
    assert!(
        result.is_err(),
        "wrong key should be rejected: {:?}",
        result
    );
}

/// Test that a token exceeding max TTL is rejected.
#[test]
fn test_token_ttl_exceeds_max() {
    let key = b"test_hmac_secret_key_32_byte_long!!";
    let claims = TokenClaims::new("user-42")
        .with_ttl(std::time::Duration::from_secs(999_999_999));

    let result = BearerToken::issue(claims, key, &TokenConfig::default(), "HS256");
    assert!(
        result.is_err(),
        "token with excessive TTL should be rejected"
    );
}

/// Test TokenClaims builder pattern.
#[test]
fn test_token_claims_builder() {
    let claims = TokenClaims::new("subject-01")
        .with_issuer("test-issuer")
        .with_audience("test-audience")
        .with_scope(vec!["read".to_string(), "write".to_string()])
        .with_not_before(1000000);

    assert_eq!(claims.sub, "subject-01");
    assert_eq!(claims.iss.as_deref(), Some("test-issuer"));
    assert_eq!(claims.aud.as_deref(), Some("test-audience"));
    assert_eq!(claims.scope.as_deref(), Some(&vec!["read".to_string(), "write".to_string()]));
    assert_eq!(claims.nbf, Some(1000000));
    assert!(claims.jti.is_some(), "jti should be auto-generated");
}

/// Test TimeWindowToken generation and verification.
#[test]
fn test_time_window_token_lifecycle() {
    let secret = [0x99; 32];
    let token = TimeWindowToken::generate(&secret, 30);

    assert_eq!(token.token.len(), 16, "token should be 16 hex chars");
    assert!(token.window_end > token.window_start);
    assert_eq!(token.window_end - token.window_start, 30);

    // Verify within same window
    let valid = TimeWindowToken::verify(&secret, &token.token, 30, 1);
    assert!(valid, "token should verify in same time window");

    // Verify with wrong secret
    let wrong_secret = [0x00; 32];
    let invalid = TimeWindowToken::verify(&wrong_secret, &token.token, 30, 1);
    assert!(!invalid, "wrong secret should not verify");
}
