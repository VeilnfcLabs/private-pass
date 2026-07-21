//! QR code generation commands.

use serde::Serialize;
use veilpass_core::qr;

#[derive(Debug, Serialize)]
pub struct QrResult {
    pub data: Vec<u8>,
    pub format: String,
    pub size: QrSize,
    pub version: u32,
}

#[derive(Debug, Serialize)]
pub struct QrSize {
    pub width: u32,
    pub height: u32,
}

/// Generate a QR code from the given content.
#[tauri::command]
#[specta::specta]
pub fn generate_qr(
    content: String,
    format: String,
    ecl: Option<String>,
    width: Option<u32>,
) -> Result<QrResult, String> {
    let ecl = match ecl.as_deref().unwrap_or("H") {
        "L" => qr::ErrorCorrectionLevel::Low,
        "M" => qr::ErrorCorrectionLevel::Medium,
        "Q" => qr::ErrorCorrectionLevel::Quartile,
        "H" => qr::ErrorCorrectionLevel::High,
        other => return Err(format!("invalid ECL: {other}")),
    };

    let output_format = match format.as_str() {
        "png" => qr::OutputFormat::Png,
        "svg" => qr::OutputFormat::Svg,
        "raw" => qr::OutputFormat::Raw,
        other => return Err(format!("unsupported format: {other}")),
    };

    let opts = qr::QrOptions {
        ecl,
        format: output_format,
        width: width.unwrap_or(512),
        margin: 4,
    };

    let output = qr::generate(&content, &opts).map_err(|e| e.to_string())?;

    match output {
        qr::QrOutput::Png(data) => Ok(QrResult {
            data,
            format: "png".to_string(),
            size: QrSize { width: opts.width, height: opts.width },
            version: 0,
        }),
        qr::QrOutput::Svg(svg) => Ok(QrResult {
            data: svg.into_bytes(),
            format: "svg".to_string(),
            size: QrSize { width: opts.width, height: opts.width },
            version: 0,
        }),
        qr::QrOutput::Raw(_) => Err("raw format not supported via IPC".to_string()),
        qr::QrOutput::Terminal(_) => Err("terminal format not supported via IPC".to_string()),
    }
}
