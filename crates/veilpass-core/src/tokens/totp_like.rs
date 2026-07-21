//! Time-window based tokens (TOTP-like).
//!
//! Provides a time-based window token similar to TOTP (RFC 6238) but built on
//! HMAC-SHA256 rather than HMAC-SHA1.  Tokens are valid only within a specific
//! time window and optionally within a configurable drift window.

use crate::Error;

/// Default time step in seconds (30 seconds, matching standard TOTP).
pub const DEFAULT_TIME_STEP: u64 = 30;

/// Default number of allowed drift windows in either direction.
pub const DEFAULT_DRIFT_WINDOWS: u32 = 1;

/// A time-window token and its window boundaries.
#[derive(Debug, Clone)]
pub struct TimeWindowToken {
    /// The token string (hex-encoded HMAC-SHA256 truncated to 8 bytes).
    pub token: String,
    /// Start of the time window (Unix timestamp, inclusive).
    pub window_start: u64,
    /// End of the time window (Unix timestamp, exclusive).
    pub window_end: u64,
    /// The counter value used for this window.
    pub counter: u64,
}

impl TimeWindowToken {
    /// Generate a time-window token for the current time.
    ///
    /// # Arguments
    /// * `secret` — 32-byte HMAC-SHA256 key.
    /// * `time_step` — Duration of each time window in seconds (default 30).
    ///
    /// The token is computed as `truncate(HMAC-SHA256(secret, counter))` where
    /// `counter = floor(current_unix_time / time_step)`.
    pub fn generate(secret: &[u8; 32], time_step: u64) -> Self {
        let now = chrono::Utc::now().timestamp() as u64;
        let time_step = time_step.max(1); // Ensure at least 1 second
        let counter = now / time_step;
        let window_start = counter * time_step;
        let window_end = window_start + time_step;

        let token = Self::compute_token(secret, counter);

        Self {
            token,
            window_start,
            window_end,
            counter,
        }
    }

    /// Verify a token against the current time window.
    ///
    /// # Arguments
    /// * `secret` — 32-byte HMAC-SHA256 key.
    /// * `token` — The token string to verify.
    /// * `time_step` — Duration of each time window in seconds.
    /// * `drift_windows` — Number of past/future windows to also accept.
    ///
    /// Returns `true` if the token is valid for any window in the range
    /// `[current_counter - drift, current_counter + drift]`.
    pub fn verify(
        secret: &[u8; 32],
        token: &str,
        time_step: u64,
        drift_windows: u32,
    ) -> bool {
        let now = chrono::Utc::now().timestamp() as u64;
        let time_step = time_step.max(1);
        let current_counter = now / time_step;

        let drift = drift_windows as i64;
        for offset in -drift..=drift {
            let check_counter = (current_counter as i64 + offset) as u64;
            let expected = Self::compute_token(secret, check_counter);
            // Constant-time comparison to prevent timing attacks
            if constant_time_eq(expected.as_bytes(), token.as_bytes()) {
                return true;
            }
        }
        false
    }

    /// Compute the HMAC-SHA256 token for a given counter value.
    ///
    /// The token is the first 8 bytes of the HMAC-SHA256 output, hex-encoded
    /// (16 hex characters).
    fn compute_token(secret: &[u8; 32], counter: u64) -> String {
        use hmac::{Hmac, Mac};
        use sha2::Sha256;

        let mut mac = Hmac::<Sha256>::new_from_slice(secret)
            .expect("HMAC should accept 32-byte key");
        mac.update(&counter.to_be_bytes());
        let result = mac.finalize();
        let bytes = result.into_bytes();

        // Truncate to 8 bytes (64 bits) — same as TOTP but using SHA-256
        hex::encode(&bytes[..8])
    }
}

/// Compare two byte slices in constant time.
fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut result: u8 = 0;
    for (x, y) in a.iter().zip(b.iter()) {
        result |= x ^ y;
    }
    result == 0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_time_window_token_generate() {
        let secret = [0xAB; 32];
        let token = TimeWindowToken::generate(&secret, DEFAULT_TIME_STEP);
        assert_eq!(token.token.len(), 16); // 8 bytes -> 16 hex chars
        assert!(token.window_end > token.window_start);
        assert_eq!(token.window_end - token.window_start, DEFAULT_TIME_STEP);
    }

    #[test]
    fn test_time_window_token_verify_valid() {
        let secret = [0x42; 32];
        let generated = TimeWindowToken::generate(&secret, DEFAULT_TIME_STEP);
        let valid = TimeWindowToken::verify(
            &secret,
            &generated.token,
            DEFAULT_TIME_STEP,
            DEFAULT_DRIFT_WINDOWS,
        );
        assert!(valid, "token should verify within same window");
    }

    #[test]
    fn test_time_window_token_wrong_secret() {
        let secret = [0xAB; 32];
        let wrong_secret = [0xCD; 32];
        let generated = TimeWindowToken::generate(&secret, DEFAULT_TIME_STEP);
        let valid = TimeWindowToken::verify(
            &wrong_secret,
            &generated.token,
            DEFAULT_TIME_STEP,
            DEFAULT_DRIFT_WINDOWS,
        );
        assert!(!valid, "wrong secret should not verify");
    }

    #[test]
    fn test_time_window_token_drift_accepts_adjacent() {
        // We can't easily test drift across time boundaries without mocking time,
        // but we can verify the logic by checking that the token for counter+1
        // is different from counter, and that verifying with drift accepts it.
        let secret = [0x11; 32];
        let now = chrono::Utc::now().timestamp() as u64;
        let counter = now / DEFAULT_TIME_STEP;

        // Token for counter + 1
        let future_token = TimeWindowToken::compute_token(&secret, counter + 1);

        // Verify with drift=1 should accept the adjacent window
        let valid = TimeWindowToken::verify(
            &secret,
            &future_token,
            DEFAULT_TIME_STEP,
            1, // drift = 1
        );
        assert!(valid, "drift=1 should accept adjacent window");

        // Verify with drift=0 should reject it
        let valid_no_drift = TimeWindowToken::verify(
            &secret,
            &future_token,
            DEFAULT_TIME_STEP,
            0,
        );
        assert!(!valid_no_drift, "drift=0 should reject adjacent window");
    }

    #[test]
    fn test_constant_time_eq_same() {
        assert!(constant_time_eq(b"hello", b"hello"));
    }

    #[test]
    fn test_constant_time_eq_different() {
        assert!(!constant_time_eq(b"hello", b"world"));
    }

    #[test]
    fn test_constant_time_eq_diff_len() {
        assert!(!constant_time_eq(b"hello", b"hello!"));
    }
}
