//! Integration tests for NFC NDEF message building and parsing.
//!
//! Tests require the `nfc` feature (enabled by default in `full`).

#![cfg(feature = "nfc")]

use veilpass_core::nfc::{NfcMessage, NfcRecordType};

/// Test creating a URI NDEF message and roundtripping through bytes.
#[test]
fn test_ndef_uri_roundtrip() {
    let uri = "https://veilpass.app/c/test-token";

    let msg = NfcMessage::uri(uri).expect("should create URI NDEF message");
    assert_eq!(msg.records.len(), 1, "should have 1 record");
    assert_eq!(msg.records[0].record_type, NfcRecordType::Uri);
    assert_eq!(msg.records[0].payload, uri);

    // Encode to bytes and decode back
    let bytes = msg.to_bytes();
    assert!(!bytes.is_empty(), "encoded bytes should not be empty");

    let decoded = NfcMessage::from_bytes(&bytes).expect("should decode NDEF bytes");
    assert_eq!(decoded.records.len(), 1, "decoded should have 1 record");
    assert_eq!(decoded.records[0].record_type, NfcRecordType::Uri);
    assert_eq!(decoded.records[0].payload, uri);
}

/// Test creating a Text NDEF message and roundtripping through bytes.
#[test]
fn test_ndef_text_roundtrip() {
    let text = "Hello, VeilPass!";
    let lang = "en";

    let msg = NfcMessage::text(text, lang).expect("should create Text NDEF message");
    assert_eq!(msg.records.len(), 1, "should have 1 record");
    assert_eq!(msg.records[0].record_type, NfcRecordType::Text);

    let bytes = msg.to_bytes();
    assert!(!bytes.is_empty(), "encoded bytes should not be empty");

    let decoded = NfcMessage::from_bytes(&bytes).expect("should decode NDEF bytes");
    assert_eq!(decoded.records.len(), 1, "decoded should have 1 record");
    assert_eq!(decoded.records[0].record_type, NfcRecordType::Text);
}

/// Test creating a Smart Poster NDEF message and roundtripping.
#[test]
fn test_ndef_smart_poster_roundtrip() {
    let title = "VeilPass Secure Link";
    let uri = "https://veilpass.app/c/secure-token-abc123";

    let msg = NfcMessage::smart_poster(title, uri)
        .expect("should create Smart Poster NDEF message");
    assert_eq!(msg.records.len(), 2, "Smart Poster should have 2 records");

    // First record should be URI
    assert_eq!(msg.records[0].record_type, NfcRecordType::Uri);
    assert_eq!(msg.records[0].payload, uri);

    // Second record should be Text (title)
    assert_eq!(msg.records[1].record_type, NfcRecordType::Text);

    let bytes = msg.to_bytes();
    assert!(!bytes.is_empty(), "encoded bytes should not be empty");

    let decoded = NfcMessage::from_bytes(&bytes).expect("should decode Smart Poster NDEF");
    assert_eq!(decoded.records.len(), 2, "decoded should have 2 records");
}

/// Test that empty URI produces an error.
#[test]
fn test_ndef_empty_uri() {
    let result = NfcMessage::uri("");
    assert!(
        result.is_err(),
        "empty URI should produce an error: {:?}",
        result
    );
}

/// Test NDEF message with very long URI.
#[test]
fn test_ndef_long_uri() {
    let long_uri = format!(
        "https://veilpass.app/c/{}",
        "a".repeat(500)
    );

    let msg = NfcMessage::uri(&long_uri).expect("long URI should succeed");
    let bytes = msg.to_bytes();
    assert!(!bytes.is_empty(), "encoded bytes should not be empty");

    let decoded = NfcMessage::from_bytes(&bytes).expect("long URI should decode");
    assert_eq!(decoded.records.len(), 1);
}

/// Test NDEF message with international text.
#[test]
fn test_ndef_international_text() {
    let text = "Привет, VeilPass! 日本語 中文";
    let lang = "en";

    let msg = NfcMessage::text(text, lang).expect("international text should succeed");
    let bytes = msg.to_bytes();
    assert!(!bytes.is_empty(), "encoded bytes should not be empty");

    let decoded = NfcMessage::from_bytes(&bytes).expect("international text should decode");
    assert_eq!(decoded.records.len(), 1);
    assert_eq!(decoded.records[0].record_type, NfcRecordType::Text);
}

/// Test multiple messages can be created independently.
#[test]
fn test_ndef_multiple_messages() {
    let uri_msg = NfcMessage::uri("https://veilpass.app/c/token-1")
        .expect("URI message");
    let text_msg = NfcMessage::text("Test payload", "en")
        .expect("Text message");

    assert_eq!(uri_msg.records.len(), 1);
    assert_eq!(text_msg.records.len(), 1);

    let uri_bytes = uri_msg.to_bytes();
    let text_bytes = text_msg.to_bytes();

    assert_ne!(uri_bytes, text_bytes, "different messages should differ");
}
