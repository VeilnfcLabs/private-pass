//! Application state for the Tauri backend.

use std::sync::Mutex;

/// Global application state.
pub struct AppState {
    /// Whether a signing key has been initialized.
    pub key_initialized: Mutex<bool>,
    /// The current key ID, if initialized.
    pub key_id: Mutex<Option<String>>,
    /// The algorithm in use.
    pub algorithm: Mutex<String>,
}

impl AppState {
    /// Create a new application state (uninitialized).
    pub fn new() -> Self {
        Self {
            key_initialized: Mutex::new(false),
            key_id: Mutex::new(None),
            algorithm: Mutex::new("EdDSA".to_string()),
        }
    }
}
