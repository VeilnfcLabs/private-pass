//! Integration tests for Ed25519 cryptographic operations with known vectors.
//!
//! Test vectors from RFC 8032 Section 7.1 — Ed25519 test vectors.
//! https://www.rfc-editor.org/rfc/rfc8032#section-7.1

use veilpass_core::signing::{Ed25519SigningKey, Ed25519VerificationKey, Signer, Verifier};

/// TEST VECTOR 1 from RFC 8032 Section 7.1.
///
/// SEED:
///   9d 61 b1 9d ef fd 5a 60 ba d4 a3 88 3c 34 df 88
///   04 e4 e9 34 31 34 fb 79 4a ac 47 5f 61 0e 1c 7d
///
/// PUBLIC KEY:
///   d7 5a 98 01 82 b1 0a b6 d5 9a 3e 85 37 4d 47 5c
///   ef 6d 69 3c 33 c3 1b 5e 3c 37 35 50 2b 1d b1 0e
///
/// MESSAGE: (empty string)
///
/// SIGNATURE:
///   e5 56 43 00 c3 48 8c e7 45 96 25 9b 1f 6b c1 09
///   e0 33 89 0c 60 47 5d 34 41 09 c4 c8 52 2f 0a 2b
///   c4 1a 23 5e 6b 38 6c ba 9b 39 4a 8a 41 b1 a0 26
///   41 52 5c 9d a5 21 05 53 45 85 30 3f 88 e6 62 c3
#[test]
fn test_rfc8032_vector_1_empty_message() {
    // Seed
    let seed: [u8; 32] = hex_literal::hex!(
        "9d61b19deffd5a60ba d4a3883c34df88"
        "04e4e9343134fb794a ac475f610e1c7d"
    );

    // Expected public key
    let expected_pk: [u8; 32] = hex_literal::hex!(
        "d75a980182b10ab6 d59a3e85374d475c"
        "ef6d693c33c31b5e 3c3735502b1db10e"
    );

    // Expected signature on empty message
    let expected_sig: [u8; 64] = hex_literal::hex!(
        "e5564300c3488ce7 4596259b1f6bc109"
        "e033890c60475d34 4109c4c8522f0a2b"
        "c41a235e6b386cba 9b394a8a41b1a026"
        "41525c9da5210553 4585303f88e662c3"
    );

    let sk = Ed25519SigningKey::from_seed(&seed);
    let vk = sk.verification_key();

    // Check public key matches
    assert_eq!(vk.to_bytes(), expected_pk, "public key mismatch");

    // Sign empty message
    let msg: &[u8] = b"";
    let sig = sk.sign(msg).expect("signing failed");

    // Check signature matches
    assert_eq!(sig.to_bytes(), expected_sig, "signature mismatch");

    // Verify with the verification key
    let result = vk.verify(msg, &sig);
    assert!(result.is_ok(), "verification should succeed");

    // Verify with the expected signature directly
    let parsed_sig = ed25519_dalek::Signature::from_slice(&expected_sig)
        .expect("valid signature bytes");
    let result = vk.verify(msg, &parsed_sig);
    assert!(result.is_ok(), "known-good signature should verify");
}

/// TEST VECTOR 2 from RFC 8032 Section 7.1.
///
/// SEED:
///   4c cd 08 9b 28 21 1b 9f 79 0b 53 80 33 3e 37 4e
///   9f 94 6a 9b d3 8d 7a 63 a4 73 a6 f6 1d 34 58 3b
///
/// PUBLIC KEY:
///   3d 40 17 c0 5e ba 6d 28 1e 16 03 6d 6c fa cd 9e
///   3e 8f 91 71 0e 39 a0 49 39 f3 3a 55 ef 3d 1a 89
///
/// MESSAGE (2 bytes): 72  f3  ("\xf3r")
///
/// SIGNATURE:
///   92 a0 09 a2 37 28 f3 4a 6c 2b b4 33 73 25 c4 d1
///   6c 04 6c f2 28 c6 54 85 55 bf 47 7d b5 1b 6f 5f
///   03 80 73 14 05 c5 6e e1 7c c6 bb 9c 5a 95 3f 54
///   86 68 1d 69 b3 69 48 5d a1 04 22 e3 e3 0c 02 c2
#[test]
fn test_rfc8032_vector_2_two_byte_message() {
    // Seed
    let seed: [u8; 32] = hex_literal::hex!(
        "4ccd089b28211b9f 790b5380333e374e"
        "9f946a9bd38d7a63 a473a6f61d34583b"
    );

    // Expected public key
    let expected_pk: [u8; 32] = hex_literal::hex!(
        "3d4017c05eba6d28 1e16036d6cfacd9e"
        "3e8f91710e39a049 39f33a55ef3d1a89"
    );

    // Expected signature on message "\xf3r" (bytes 0x72, 0xf3)
    let expected_sig: [u8; 64] = hex_literal::hex!(
        "92a009a23728f34a 6c2bb4337325c4d1"
        "6c046cf228c65485 55bf477db51b6f5f"
        "0380731405c56ee1 7cc6bb9c5a953f54"
        "86681d69b369485d a10422e3e30c02c2"
    );

    let sk = Ed25519SigningKey::from_seed(&seed);
    let vk = sk.verification_key();

    assert_eq!(vk.to_bytes(), expected_pk, "public key mismatch");

    let msg: &[u8] = &[0x72, 0xf3];
    let sig = sk.sign(msg).expect("signing failed");

    assert_eq!(sig.to_bytes(), expected_sig, "signature mismatch");

    let result = vk.verify(msg, &sig);
    assert!(result.is_ok(), "verification should succeed");
}

/// Test that key generation produces valid keys.
#[test]
fn test_random_key_generates_valid_keys() {
    let sk = Ed25519SigningKey::generate();
    let vk = sk.verification_key();

    let msg = b"test message for random key";
    let sig = sk.sign(msg).expect("signing failed");
    assert!(vk.verify(msg, &sig).is_ok(), "self-verification should succeed");
}

/// Test that tampered messages are rejected.
#[test]
fn test_tampered_message_rejected() {
    let sk = Ed25519SigningKey::generate();
    let vk = sk.verification_key();

    let msg = b"original message";
    let sig = sk.sign(msg).expect("signing failed");

    let tampered = b"tampered message";
    assert!(vk.verify(tampered, &sig).is_err(), "tampered message should be rejected");
}

/// Test that signatures from different keys are rejected.
#[test]
fn test_wrong_key_rejected() {
    let sk1 = Ed25519SigningKey::generate();
    let sk2 = Ed25519SigningKey::generate();

    let msg = b"some message";
    let sig = sk1.sign(msg).expect("signing failed");

    assert!(
        sk2.verification_key().verify(msg, &sig).is_err(),
        "signature from different key should be rejected"
    );
}

/// Test HMAC-SHA256 sign/verify with known approach.
#[test]
fn test_hmac_sign_verify_roundtrip() {
    use veilpass_core::signing::{HmacSha256Key, Signer, Verifier};

    let key = HmacSha256Key::generate();
    let msg = b"hmac test message";
    let sig = key.sign(msg).expect("hmac signing failed");
    assert!(key.verify(msg, &sig).is_ok(), "hmac verification should succeed");
}

/// Test HMAC-SHA256 wrong key rejection.
#[test]
fn test_hmac_wrong_key_rejection() {
    use veilpass_core::signing::{HmacSha256Key, Signer, Verifier};

    let key1 = HmacSha256Key::generate();
    let key2 = HmacSha256Key::generate();

    let msg = b"message";
    let sig = key1.sign(msg).expect("signing failed");
    assert!(key2.verify(msg, &sig).is_err(), "wrong key should reject");
}
