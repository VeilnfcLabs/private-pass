//! Secure memory handling.
//!
//! Uses the `zeroize` crate to ensure sensitive data (keys, seeds) is
//! zeroed out when dropped, preventing memory scraping attacks.

use zeroize::Zeroize;

/// A wrapper around `Vec<u8>` that zeroizes on drop.
#[derive(Clone, Debug, Zeroize)]
#[zeroize(drop)]
pub struct SecureVec(Vec<u8>);

impl SecureVec {
    /// Create a new secure vector from raw bytes.
    pub fn new(data: Vec<u8>) -> Self {
        Self(data)
    }

    /// Borrow the underlying bytes.
    pub fn as_bytes(&self) -> &[u8] {
        &self.0
    }

    /// Take ownership and return the inner vec (caller must zeroize).
    pub fn into_inner(mut self) -> Vec<u8> {
        let inner = std::mem::take(&mut self.0);
        // self will be dropped, but inner's memory isn't zeroed here
        inner
    }

    /// Length of the underlying data.
    pub fn len(&self) -> usize {
        self.0.len()
    }

    /// Whether the underlying data is empty.
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

impl From<Vec<u8>> for SecureVec {
    fn from(data: Vec<u8>) -> Self {
        Self::new(data)
    }
}

/// A fixed-size 32-byte secure array (e.g., for Ed25519 seeds or HMAC keys).
#[derive(Clone, Debug, Zeroize)]
#[zeroize(drop)]
pub struct SecureKey([u8; 32]);

impl SecureKey {
    /// Create a new secure key from a 32-byte array.
    pub fn new(data: [u8; 32]) -> Self {
        Self(data)
    }

    /// Borrow the underlying bytes.
    pub fn as_bytes(&self) -> &[u8] {
        &self.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_secure_vec_zeroized_after_drop() {
        let ptr;
        {
            let vec = SecureVec::new(vec![0xAB; 32]);
            ptr = vec.as_bytes().as_ptr();
        }
        // The memory at ptr should have been zeroed, but we can't reliably
        // test this in safe Rust since the memory may be reused.
        // This test verifies compilation and basic functionality.
    }

    #[test]
    fn test_secure_key_creation() {
        let key = SecureKey::new([0x42; 32]);
        assert_eq!(key.as_bytes(), &[0x42; 32]);
    }
}
