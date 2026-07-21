//! Key management commands.

use serde::Serialize;
use veilpass_core::signing::Ed25519SigningKey;

use crate::state::AppState;
use crate::error::{AppError, AppResult, into_app_result};

#[derive(Debug, Serialize)]
pub struct KeyInfo {
    pub algorithm: String,
    pub public_key: String,
    pub key_id: String,
    pub created_at: String,
}

/// Initialize a new signing key.
#[tauri::command]
#[specta::specta]
pub fn initialize_key(
    state: tauri::State<'_, AppState>,
    algorithm: Option<String>,
) -> AppResult<KeyInfo> {
    into_app_result(initialize_key_inner(state, algorithm))
}

fn initialize_key_inner(
    state: tauri::State<'_, AppState>,
    algorithm: Option<String>,
) -> Result<KeyInfo, AppError> {
    let alg = algorithm.unwrap_or_else(|| "EdDSA".to_string());

    let (public_key_hex, key_id) = match alg.to_uppercase().as_str() {
        "EDDSA" | "ED25519" => {
            let key = Ed25519SigningKey::generate();
            let pk = key.verification_key();
            let kid = pk.key_id();
            (hex::encode(pk.to_bytes()), kid)
        }
        _ => return Err(AppError::InvalidInput(format!("unsupported algorithm: {alg}"))),
    };

    // Update state
    if let Ok(mut initialized) = state.key_initialized.lock() {
        *initialized = true;
    }
    if let Ok(mut kid) = state.key_id.lock() {
        *kid = Some(key_id.clone());
    }
    if let Ok(mut a) = state.algorithm.lock() {
        *a = alg.clone();
    }

    Ok(KeyInfo {
        algorithm: alg,
        public_key: public_key_hex,
        key_id,
        created_at: chrono::Utc::now().to_rfc3339(),
    })
}

/// Get information about the current signing key.
#[tauri::command]
#[specta::specta]
pub fn get_key_info(
    state: tauri::State<'_, AppState>,
) -> AppResult<Option<KeyInfo>> {
    let initialized = state.key_initialized.lock().map_err(|e| e.to_string())?;
    if !*initialized {
        return Ok(None);
    }

    let kid = state.key_id.lock().map_err(|e| e.to_string())?;
    let algorithm = state.algorithm.lock().map_err(|e| e.to_string())?;

    Ok(Some(KeyInfo {
        algorithm: algorithm.clone(),
        public_key: "stored_in_keychain".to_string(),
        key_id: kid.clone().unwrap_or_default(),
        created_at: chrono::Utc::now().to_rfc3339(),
    }))
}

/// Export the signing key as an encrypted bundle.
#[tauri::command]
#[specta::specta]
pub fn export_key(
    _state: tauri::State<'_, AppState>,
    _passphrase: String,
) -> AppResult<Vec<u8>> {
    Err("Key export not yet implemented".to_string())
}

/// Import a signing key from an encrypted bundle.
#[tauri::command]
#[specta::specta]
pub fn import_key(
    _state: tauri::State<'_, AppState>,
    _data: Vec<u8>,
    _passphrase: String,
) -> AppResult<()> {
    Err("Key import not yet implemented".to_string())
}
