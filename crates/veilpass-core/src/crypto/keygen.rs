//! Key generation and derivation utilities.
//!
//! Generates Ed25519 key pairs and HMAC-SHA256 symmetric keys
//! using the operating system's CSPRNG.  Also provides HKDF-based
//! key derivation for deriving sub-keys from a master secret.

use crate::Result;
use crate::crypto::Algorithm;

/// Generate a cryptographically secure random byte vector of the given length.
pub fn generate_random_bytes(length: usize) -> Vec<u8> {
    use rand::RngCore;
    let mut bytes = vec![0u8; length];
    rand::thread_rng().fill_bytes(&mut bytes);
    bytes
}

/// Generate a key seed for the specified algorithm.
pub fn generate_key_seed(algorithm: Algorithm) -> Vec<u8> {
    generate_random_bytes(algorithm.key_size())
}

/// Derive a key of the given length using HKDF-SHA256.
///
/// HKDF (HMAC-based Key Derivation Function, RFC 5869) takes:
/// - `ikm` — Input keying material (the source entropy)
/// - `salt` — Optional salt (randomize output; use empty slice for no salt)
/// - `info` — Optional context string (bind derived key to a specific purpose)
/// - `derived_len` — Desired output length in bytes
///
/// # Errors
///
/// Returns `CryptoError` if the HKDF expansion step fails (should never
/// happen with valid input, but propagated for correctness).
///
/// # Example
///
/// ```ignore
/// let master_secret = b"some shared secret";
/// let encryption_key = derive_key_hkdf(master_secret, b"random-salt", b"encryption", 32)?;
/// let signing_key = derive_key_hkdf(master_secret, b"random-salt", b"signing", 32)?;
/// ```
pub fn derive_key_hkdf(
    ikm: &[u8],
    salt: &[u8],
    info: &[u8],
    derived_len: usize,
) -> Result<Vec<u8>> {
    use hkdf::Hkdf;
    use sha2::Sha256;

    let hk = if salt.is_empty() {
        // HKDF extract-then-expand with zero-length salt (using a string of
        // `HashLen` zeros implicitly as defined in RFC 5869 Section 2.2).
        Hkdf::<Sha256>::new(None, ikm)
    } else {
        Hkdf::<Sha256>::new(Some(salt), ikm)
    };

    let mut okm = vec![0u8; derived_len];
    hk.expand(info, &mut okm)
        .map_err(|e| crate::Error::Crypto(format!("HKDF expansion failed: {e}")))?;

    Ok(okm)
}

/// Derive an Ed25519 seed (32 bytes) from a master secret using HKDF.
///
/// This is useful when you want to deterministically derive Ed25519 keys
/// from a master secret without storing multiple private keys.
///
/// # Arguments
/// * `master_secret` — The source keying material.
/// * `salt` — Optional salt for domain separation.
/// * `context` — Optional context string (e.g., "veilpass-ed25519-key-1").
pub fn derive_ed25519_seed(
    master_secret: &[u8],
    salt: &[u8],
    context: &[u8],
) -> Result<[u8; 32]> {
    let derived = derive_key_hkdf(master_secret, salt, context, 32)?;
    let mut seed = [0u8; 32];
    seed.copy_from_slice(&derived);
    Ok(seed)
}

/// Derive an HMAC-SHA256 key (32 bytes) from a master secret using HKDF.
///
/// # Arguments
/// * `master_secret` — The source keying material.
/// * `salt` — Optional salt for domain separation.
/// * `context` — Optional context string (e.g., "veilpass-hmac-key-1").
pub fn derive_hmac_key(
    master_secret: &[u8],
    salt: &[u8],
    context: &[u8],
) -> Result<[u8; 32]> {
    let derived = derive_key_hkdf(master_secret, salt, context, 32)?;
    let mut key = [0u8; 32];
    key.copy_from_slice(&derived);
    Ok(key)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_random_bytes_length() {
        let bytes = generate_random_bytes(32);
        assert_eq!(bytes.len(), 32);
    }

    #[test]
    fn test_generate_random_bytes_entropy() {
        let a = generate_random_bytes(32);
        let b = generate_random_bytes(32);
        // Extremely unlikely to collide
        assert_ne!(a, b);
    }

    #[test]
    fn test_generate_key_seed_ed25519() {
        let seed = generate_key_seed(Algorithm::Ed25519);
        assert_eq!(seed.len(), 32);
    }

    #[test]
    fn test_generate_key_seed_hs256() {
        let seed = generate_key_seed(Algorithm::Hs256);
        assert_eq!(seed.len(), 32);
    }

    #[test]
    fn test_derive_key_hkdf_basic() {
        let ikm = b"master-secret-42";
        let derived = derive_key_hkdf(ikm, b"salt", b"test-context", 32)
            .expect("HKDF derivation should succeed");
        assert_eq!(derived.len(), 32);
    }

    #[test]
    fn test_derive_key_hkdf_deterministic() {
        let ikm = b"same-master-secret";
        let a = derive_key_hkdf(ikm, b"salt", b"ctx", 32).unwrap();
        let b = derive_key_hkdf(ikm, b"salt", b"ctx", 32).unwrap();
        assert_eq!(a, b, "same inputs should produce same output");
    }

    #[test]
    fn test_derive_key_hkdf_different_context() {
        let ikm = b"master-secret";
        let a = derive_key_hkdf(ikm, b"salt", b"context-A", 32).unwrap();
        let b = derive_key_hkdf(ikm, b"salt", b"context-B", 32).unwrap();
        assert_ne!(a, b, "different contexts should produce different keys");
    }

    #[test]
    fn test_derive_key_hkdf_different_salt() {
        let ikm = b"master-secret";
        let a = derive_key_hkdf(ikm, b"salt-A", b"ctx", 32).unwrap();
        let b = derive_key_hkdf(ikm, b"salt-B", b"ctx", 32).unwrap();
        assert_ne!(a, b, "different salts should produce different keys");
    }

    #[test]
    fn test_derive_key_hkdf_variable_lengths() {
        let ikm = b"master-secret";
        for len in &[16, 32, 64, 128] {
            let derived = derive_key_hkdf(ikm, b"salt", b"ctx", *len)
                .unwrap_or_else(|_| panic!("derivation for len {} should succeed", len));
            assert_eq!(derived.len(), *len);
        }
    }

    #[test]
    fn test_derive_key_hkdf_no_salt() {
        let ikm = b"master-secret";
        let derived = derive_key_hkdf(ikm, &[], b"ctx", 32)
            .expect("derivation without salt should succeed");
        assert_eq!(derived.len(), 32);

        // Same inputs without salt should be deterministic
        let derived2 = derive_key_hkdf(ikm, &[], b"ctx", 32).unwrap();
        assert_eq!(derived, derived2);
    }

    #[test]
    fn test_derive_ed25519_seed() {
        let master = b"master-secret-for-ed25519";
        let seed = derive_ed25519_seed(master, b"salt", b"ed25519-key-1")
            .expect("Ed25519 seed derivation should succeed");
        assert_eq!(seed.len(), 32);

        // Should be deterministic
        let seed2 = derive_ed25519_seed(master, b"salt", b"ed25519-key-1").unwrap();
        assert_eq!(seed, seed2);

        // Different context should produce different seed
        let seed3 = derive_ed25519_seed(master, b"salt", b"ed25519-key-2").unwrap();
        assert_ne!(seed, seed3);
    }

    #[test]
    fn test_derive_hmac_key() {
        let master = b"master-secret-for-hmac";
        let key = derive_hmac_key(master, b"salt", b"hmac-key-1")
            .expect("HMAC key derivation should succeed");
        assert_eq!(key.len(), 32);

        // Should be deterministic
        let key2 = derive_hmac_key(master, b"salt", b"hmac-key-1").unwrap();
        assert_eq!(key, key2);
    }

    #[test]
    fn test_derived_ed25519_key_signs() {
        use crate::signing::{Ed25519SigningKey, Signer};

        let master = b"master-secret-for-signing-test";
        let seed = derive_ed25519_seed(master, b"salt", b"test-key").unwrap();
        let sk = Ed25519SigningKey::from_seed(&seed);
        let msg = b"test message with derived key";
        let sig = sk.sign(msg).expect("signing should succeed");
        assert!(
            sk.verification_key().verify(msg, &sig).is_ok(),
            "verification should succeed"
        );
    }
}
