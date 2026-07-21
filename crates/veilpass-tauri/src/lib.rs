//! VeilPass Tauri backend — Desktop app logic.

pub mod commands;
pub mod error;
pub mod state;

use state::AppState;

/// Run the Tauri application.
pub fn run() {
    tracing_subscriber::fmt::init();

    tauri::Builder::default()
        .manage(AppState::new())
        .invoke_handler(tauri::generate_handler![
            // QR commands
            commands::qr::generate_qr,
            // NFC commands
            commands::nfc::generate_ndef,
            // Link commands
            commands::links::create_claim_link,
            commands::links::verify_claim_link,
            // Sign commands
            commands::sign::sign_url,
            // Token commands
            commands::tokens::issue_token,
            commands::tokens::verify_token,
            // Key commands
            commands::keys::initialize_key,
            commands::keys::get_key_info,
            commands::keys::export_key,
            commands::keys::import_key,
        ])
        .run(tauri::generate_context!())
        .expect("error while running VeilPass");
}
