//! NFC NDEF record generation module.
//!
//! Provides types and functions for building NDEF (NFC Data Exchange Format)
//! messages that can be written to NFC tags.

#[cfg(feature = "nfc")]
mod nfc_impl {
    use ndef_rs::{NdefMessage, NdefRecord, TNF};
    use ndef_rs::payload::UriPayload;
    use crate::Error;

    /// An NDEF message, containing one or more records.
    pub struct NfcMessage {
        inner: NdefMessage,
        /// Human-readable description of records.
        pub records: Vec<NfcRecordInfo>,
    }

    /// Information about an NDEF record.
    #[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
    pub struct NfcRecordInfo {
        /// Record type.
        pub record_type: NfcRecordType,
        /// Payload summary.
        pub payload: String,
    }

    /// Supported NDEF record types.
    #[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
    #[serde(rename_all = "snake_case")]
    pub enum NfcRecordType {
        /// URI record (e.g., https://...).
        Uri,
        /// Text record.
        Text,
        /// MIME type record.
        Mime,
        /// Smart Poster (title + URI).
        SmartPoster,
    }

    impl NfcMessage {
        /// Create an NDEF message containing a single URI record.
        pub fn uri(uri: &str) -> crate::Result<Self> {
            let payload = UriPayload::from_str(uri)
                .map_err(|e| Error::Nfc(format!("invalid URI: {e}")))?;

            let record = NdefRecord::builder()
                .tnf(TNF::WellKnown)
                .payload(&payload)
                .build()
                .map_err(|e| Error::Nfc(e.to_string()))?;

            let inner = NdefMessage::from(&[record]);

            Ok(Self {
                inner,
                records: vec![NfcRecordInfo {
                    record_type: NfcRecordType::Uri,
                    payload: uri.to_string(),
                }],
            })
        }

        /// Create an NDEF message containing a text record.
        pub fn text(text: &str, language: &str) -> crate::Result<Self> {
            // Use ndef_rs text payload
            let payload = ndef_rs::payload::TextPayload::new(text, language);

            let record = NdefRecord::builder()
                .tnf(TNF::WellKnown)
                .payload(&payload)
                .build()
                .map_err(|e| Error::Nfc(e.to_string()))?;

            let inner = NdefMessage::from(&[record]);

            Ok(Self {
                inner,
                records: vec![NfcRecordInfo {
                    record_type: NfcRecordType::Text,
                    payload: format!("[{}] {}", language, text),
                }],
            })
        }

        /// Create an NDEF message with a Smart Poster (title + URI).
        pub fn smart_poster(title: &str, uri: &str) -> crate::Result<Self> {
            // A Smart Poster typically contains multiple records:
            // 1. A URI record
            // 2. A Text record (title)
            // For simplicity, we create a message with both records.

            let uri_payload = UriPayload::from_str(uri)
                .map_err(|e| Error::Nfc(format!("invalid URI: {e}")))?;

            let uri_record = NdefRecord::builder()
                .tnf(TNF::WellKnown)
                .payload(&uri_payload)
                .build()
                .map_err(|e| Error::Nfc(e.to_string()))?;

            let text_payload = ndef_rs::payload::TextPayload::new(title, "en");
            let text_record = NdefRecord::builder()
                .tnf(TNF::WellKnown)
                .payload(&text_payload)
                .build()
                .map_err(|e| Error::Nfc(e.to_string()))?;

            let inner = NdefMessage::from(&[uri_record, text_record]);

            Ok(Self {
                inner,
                records: vec![
                    NfcRecordInfo {
                        record_type: NfcRecordType::Uri,
                        payload: uri.to_string(),
                    },
                    NfcRecordInfo {
                        record_type: NfcRecordType::Text,
                        payload: title.to_string(),
                    },
                ],
            })
        }

        /// Encode the NDEF message to bytes (ready for writing to an NFC tag).
        pub fn to_bytes(&self) -> Vec<u8> {
            self.inner.to_buffer().unwrap_or_default()
        }

        /// Parse NDEF bytes back into a message.
        pub fn from_bytes(data: &[u8]) -> crate::Result<Self> {
            let inner = NdefMessage::decode(data)
                .map_err(|e| Error::Nfc(format!("NDEF decode failed: {e}")))?;

            // Extract record info
            let mut records = Vec::new();
            for record in inner.iter() {
                // Attempt to determine record type
                let (record_type, payload) = match record.tnf() {
                    TNF::WellKnown => {
                        if let Ok(text) = ndef_rs::payload::TextPayload::try_from(record) {
                            (NfcRecordType::Text, text.text().to_string())
                        } else if let Ok(uri) = UriPayload::try_from(record) {
                            (NfcRecordType::Uri, uri.uri().to_string())
                        } else {
                            (NfcRecordType::Mime, format!("{:?}", record.payload()))
                        }
                    }
                    _ => (NfcRecordType::Mime, format!("{:?}", record.payload())),
                };
                records.push(NfcRecordInfo { record_type, payload });
            }

            Ok(Self { inner, records })
        }
    }
}

#[cfg(not(feature = "nfc"))]
mod nfc_stub {}

#[cfg(feature = "nfc")]
pub use nfc_impl::*;
