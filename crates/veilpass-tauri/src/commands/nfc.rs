//! NFC NDEF generation commands.

use serde::Serialize;
use veilpass_core::nfc;

#[derive(Debug, Serialize)]
pub struct NdefResult {
    pub bytes: Vec<u8>,
    pub records: Vec<NdefRecordInfo>,
}

#[derive(Debug, Serialize)]
pub struct NdefRecordInfo {
    pub record_type: String,
    pub payload: String,
}

/// Generate an NFC NDEF payload.
#[tauri::command]
#[specta::specta]
pub fn generate_ndef(
    record_type: String,
    content: String,
    title: Option<String>,
    language: Option<String>,
) -> Result<NdefResult, String> {
    let message = match record_type.as_str() {
        "uri" => nfc::NfcMessage::uri(&content).map_err(|e| e.to_string())?,
        "text" => nfc::NfcMessage::text(&content, language.as_deref().unwrap_or("en"))
            .map_err(|e| e.to_string())?,
        "smart_poster" => nfc::NfcMessage::smart_poster(
            title.as_deref().unwrap_or("Smart Poster"),
            &content,
        ).map_err(|e| e.to_string())?,
        other => return Err(format!("unsupported NDEF record type: {other}")),
    };

    let records = message.records.iter().map(|r| NdefRecordInfo {
        record_type: format!("{:?}", r.record_type),
        payload: r.payload.clone(),
    }).collect();

    Ok(NdefResult {
        bytes: message.to_bytes(),
        records,
    })
}
