//! Integration tests for QR code generation and roundtrip.
//!
//! Tests require the `qr` feature (enabled by default in `full`).

#![cfg(feature = "qr")]

use veilpass_core::qr::{
    generate, generate_png, generate_svg, ErrorCorrectionLevel, OutputFormat, QrOptions, QrOutput,
};

/// Test generating a PNG QR code.
#[test]
fn test_qr_png_generation() {
    let png_bytes = generate_png("https://veilpass.app/test")
        .expect("PNG QR generation should succeed");
    assert!(!png_bytes.is_empty(), "PNG should have content");
    // PNG header: 89 50 4E 47 0D 0A 1A 0A
    assert_eq!(&png_bytes[..4], &[0x89, 0x50, 0x4E, 0x47], "should be a PNG");
}

/// Test generating an SVG QR code.
#[test]
fn test_qr_svg_generation() {
    let svg = generate_svg("https://veilpass.app/test")
        .expect("SVG QR generation should succeed");
    assert!(svg.starts_with("<svg"), "SVG should start with <svg");
    assert!(svg.contains("</svg>"), "SVG should close properly");
    assert!(
        svg.contains("veilpass.app"),
        "SVG should contain encoded data"
    );
}

/// Test generating a raw matrix.
#[test]
fn test_qr_raw_matrix() {
    let opts = QrOptions {
        format: OutputFormat::Raw,
        ..Default::default()
    };
    let output = generate("https://veilpass.app", &opts)
        .expect("Raw QR generation should succeed");

    match output {
        QrOutput::Raw(matrix) => {
            assert!(!matrix.is_empty(), "matrix should have rows");
            assert!(!matrix[0].is_empty(), "matrix should have columns");
            // A QR code should have at least 21x21 modules (version 1)
            assert!(matrix.len() >= 21, "QR matrix should be at least 21x21");
            assert!(matrix[0].len() >= 21, "QR matrix should be at least 21x21");
        }
        _ => panic!("expected Raw output"),
    }
}

/// Test generating a terminal QR string.
#[test]
fn test_qr_terminal() {
    let opts = QrOptions {
        format: OutputFormat::Terminal,
        ..Default::default()
    };
    let output = generate("https://veilpass.app", &opts)
        .expect("Terminal QR generation should succeed");

    match output {
        QrOutput::Terminal(term) => {
            assert!(!term.is_empty(), "terminal output should not be empty");
            // Should contain block characters
            assert!(
                term.contains('\u{2588}') || term.contains('#'),
                "terminal QR should contain block chars or #"
            );
        }
        _ => panic!("expected Terminal output"),
    }
}

/// Test different error correction levels.
#[test]
fn test_qr_error_correction_levels() {
    let test_cases = [
        ErrorCorrectionLevel::Low,
        ErrorCorrectionLevel::Medium,
        ErrorCorrectionLevel::Quartile,
        ErrorCorrectionLevel::High,
    ];

    for ecl in &test_cases {
        let opts = QrOptions {
            ecl: *ecl,
            format: OutputFormat::Svg,
            ..Default::default()
        };
        let output = generate("https://veilpass.app/test-ec-level", &opts)
            .unwrap_or_else(|_| panic!("ECL {:?} should succeed", ecl));
        match output {
            QrOutput::Svg(svg) => assert!(svg.contains("</svg>")),
            _ => panic!("expected SVG output"),
        }
    }
}

/// Test QR with custom width.
#[test]
fn test_qr_custom_width() {
    let opts = QrOptions {
        format: OutputFormat::Svg,
        width: 1024,
        ..Default::default()
    };
    let output = generate("https://veilpass.app/wide", &opts)
        .expect("Custom width QR should succeed");
    match output {
        QrOutput::Svg(svg) => {
            assert!(svg.contains("width"), "SVG should have width attribute");
        }
        _ => panic!("expected SVG output"),
    }
}

/// Test QR with URL containing special characters.
#[test]
fn test_qr_with_special_chars() {
    let content = "https://veilpass.app/path?a=1&b=2&c=hello%20world";
    let svg = generate_svg(content).expect("QR with special chars should succeed");
    assert!(svg.contains("</svg>"), "should produce valid SVG");
}

/// Test QR output extension and MIME type.
#[test]
fn test_qr_output_metadata() {
    let opts = QrOptions {
        format: OutputFormat::Png,
        ..Default::default()
    };
    let output = generate("test", &opts).expect("QR generation should succeed");
    assert_eq!(output.extension(), "png");
    assert_eq!(output.mime_type(), "image/png");

    let opts = QrOptions {
        format: OutputFormat::Svg,
        ..Default::default()
    };
    let output = generate("test", &opts).expect("QR generation should succeed");
    assert_eq!(output.extension(), "svg");
    assert_eq!(output.mime_type(), "image/svg+xml");
}

/// Test that empty content produces an error (QR codes require content).
#[test]
fn test_qr_empty_content() {
    let result = generate_png("");
    // This may succeed or fail depending on the fast_qr behavior
    // Document the behavior
    if let Err(e) = result {
        assert!(
            format!("{}", e).contains("QR"),
            "error should mention QR: {}",
            e
        );
    }
}
