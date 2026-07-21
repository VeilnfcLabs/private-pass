//! QR code generation module.
//!
//! Wraps the `fast_qr` crate with VeilPass-specific options and output types.

#[cfg(feature = "qr")]
mod qr_impl {
    use fast_qr::convert::{svg::SvgBuilder, Builder, Shape};
    use fast_qr::qr::QRBuilder;
    use crate::Error;

    /// Error correction levels for QR codes.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub enum ErrorCorrectionLevel {
        /// Low — recovers 7% of data.
        Low,
        /// Medium — recovers 15% of data.
        Medium,
        /// Quartile — recovers 25% of data.
        Quartile,
        /// High — recovers 30% of data (DEFAULT).
        High,
    }

    impl From<ErrorCorrectionLevel> for fast_qr::qr::ECL {
        fn from(ecl: ErrorCorrectionLevel) -> Self {
            match ecl {
                ErrorCorrectionLevel::Low => fast_qr::qr::ECL::L,
                ErrorCorrectionLevel::Medium => fast_qr::qr::ECL::M,
                ErrorCorrectionLevel::Quartile => fast_qr::qr::ECL::Q,
                ErrorCorrectionLevel::High => fast_qr::qr::ECL::H,
            }
        }
    }

    /// Output format for QR codes.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub enum OutputFormat {
        /// Portable Network Graphics (PNG) — raster image.
        Png,
        /// Scalable Vector Graphics (SVG) — vector image.
        Svg,
        /// Raw boolean matrix (for custom rendering).
        Raw,
        /// Terminal Unicode output.
        Terminal,
    }

    /// Options for QR code generation.
    #[derive(Debug, Clone)]
    pub struct QrOptions {
        /// Error correction level (default: High).
        pub ecl: ErrorCorrectionLevel,
        /// Output format (default: Png).
        pub format: OutputFormat,
        /// Width of the output image in pixels (PNG/SVG only).
        pub width: u32,
        /// Quiet zone margin in modules (default: 4).
        pub margin: u8,
    }

    impl Default for QrOptions {
        fn default() -> Self {
            Self {
                ecl: ErrorCorrectionLevel::High,
                format: OutputFormat::Png,
                width: 512,
                margin: 4,
            }
        }
    }

    /// Generated QR code output.
    #[derive(Debug, Clone)]
    pub enum QrOutput {
        /// PNG image bytes.
        Png(Vec<u8>),
        /// SVG XML string.
        Svg(String),
        /// Raw boolean matrix (rows of modules).
        Raw(Vec<Vec<bool>>),
        /// Terminal Unicode string.
        Terminal(String),
    }

    impl QrOutput {
        /// Get the output as PNG bytes (panics if not PNG format).
        pub fn into_png(self) -> Vec<u8> {
            match self {
                QrOutput::Png(bytes) => bytes,
                _ => panic!("output is not PNG"),
            }
        }

        /// Get the output as SVG string (panics if not SVG format).
        pub fn into_svg(self) -> String {
            match self {
                QrOutput::Svg(s) => s,
                _ => panic!("output is not SVG"),
            }
        }

        /// Get the output file extension.
        pub fn extension(&self) -> &'static str {
            match self {
                QrOutput::Png(_) => "png",
                QrOutput::Svg(_) => "svg",
                QrOutput::Raw(_) => "txt",
                QrOutput::Terminal(_) => "txt",
            }
        }

        /// Get the MIME type.
        pub fn mime_type(&self) -> &'static str {
            match self {
                QrOutput::Png(_) => "image/png",
                QrOutput::Svg(_) => "image/svg+xml",
                QrOutput::Raw(_) => "text/plain",
                QrOutput::Terminal(_) => "text/plain",
            }
        }
    }

    /// Generate a QR code with the given content and options.
    pub fn generate(content: &str, opts: &QrOptions) -> crate::Result<QrOutput> {
        let qr = QRBuilder::new(content)
            .ecl(opts.ecl.into())
            .build()
            .map_err(|e| Error::Qr(e.to_string()))?;

        match opts.format {
            OutputFormat::Svg => {
                let svg = SvgBuilder::default()
                    .shape(Shape::Square)
                    .background_color([255, 255, 255, 0])
                    .fit_width(opts.width)
                    .to_str(&qr);
                Ok(QrOutput::Svg(svg))
            }
            OutputFormat::Png => {
                #[cfg(feature = "image")]
                {
                    let img = fast_qr::convert::image::ImageBuilder::default()
                        .shape(Shape::Square)
                        .background_color([255, 255, 255, 255])
                        .fit_width(opts.width)
                        .to_png(&qr)
                        .map_err(|e| Error::Qr(e.to_string()))?;
                    Ok(QrOutput::Png(img))
                }
                #[cfg(not(feature = "image"))]
                {
                    // Fallback: return SVG wrapped as PNG stub
                    Err(Error::Qr("PNG output requires the 'image' feature".into()))
                }
            }
            OutputFormat::Raw => {
                let matrix = qr.to_matrix();
                Ok(QrOutput::Raw(matrix))
            }
            OutputFormat::Terminal => {
                let term = qr.to_str();
                Ok(QrOutput::Terminal(term))
            }
        }
    }

    /// Convenience function: generate a PNG QR code with default options.
    pub fn generate_png(content: &str) -> crate::Result<Vec<u8>> {
        let output = generate(content, &QrOptions {
            format: OutputFormat::Png,
            ..Default::default()
        })?;
        Ok(output.into_png())
    }

    /// Convenience function: generate an SVG QR code with default options.
    pub fn generate_svg(content: &str) -> crate::Result<String> {
        let output = generate(content, &QrOptions {
            format: OutputFormat::Svg,
            ..Default::default()
        })?;
        Ok(output.into_svg())
    }
}

#[cfg(not(feature = "qr"))]
mod qr_stub {}

#[cfg(feature = "qr")]
pub use qr_impl::*;
