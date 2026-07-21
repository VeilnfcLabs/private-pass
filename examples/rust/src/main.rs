// VeilPass API — Rust example
//
// Demonstrates all 6 API operations using reqwest with serde for JSON.
// Run: cargo run

use reqwest::Client;
use serde_json::{json, Value};
use std::env;
use std::time::Duration;

// ── Configuration ──────────────────────────────────────────────────────────────

struct Config {
    base_url: String,
    api_key: String,
}

impl Config {
    fn from_env() -> Self {
        Self {
            base_url: env_or("VEILPASS_API_URL", "http://localhost:8000"),
            api_key: env_or("VEILPASS_API_KEY", ""),
        }
    }
}

fn env_or(key: &str, fallback: &str) -> String {
    std::env::var(key).unwrap_or_else(|_| fallback.to_string())
}

// ── Helpers ────────────────────────────────────────────────────────────────────

fn log(label: &str, data: &serde_json::Value) {
    println!("\n── {label} ──");
    println!("{}", serde_json::to_string_pretty(data).unwrap());
}

// ── 1. QR Generation ────────────────────────────────────────────────────────────

async fn generate_qr(client: &Client) -> Result<Value, Error> {
    let res = client
        .post("/api/v1/qr")
        .header("Accept", "application/json")
        .json(&json!({
            "content": "https://veilpass.app",
            "format": "png",
            "ecl": "H",
            "size": 512,
            "margin": 4,
            "color": "#000000",
            "bg_color": "#FFFFFF",
            "include_logo": false,
            "one_time": false,
            "expires_in": null,
        }))
        .send()
        .await?;

    let data: Value = res.json().await?;
    log("QR Generation", &data);
    Ok(data)
}

// ── 2. NFC Payload ──────────────────────────────────────────────────────────────

async fn generate_nfc(client: &Client) -> Result<Value, Error> {
    let res = client
        .post("/api/v1/nfc")
        .json(&json!({
            "issuer": "veilpass",
            "payload": "https://veilpass.app/contact",
            "version": "1.0",
            "type": "uri",
            "expiration": null,
            "metadata": { "department": "engineering" },
        }))
        .send()
        .await?;

    let data: Value = res.json().await?;
    log("NFC Payload", &data);
    Ok(data)
}

// ── 3. Signed Link ─────────────────────────────────────────────────────────────

async fn create_signed_link(client: &Client) -> Result<Value, Error> {
    let res = client
        .post("/api/v1/signed-link")
        .json(&json!({
            "resource": "documents/nda-q3-2026.pdf",
            "ttl": 86400,
            "one_time": true,
            "max_uses": 5,
        }))
        .send()
        .await?;

    let data: Value = res.json().await?;
    log("Signed Link", &data);
    Ok(data)
}

// ── 4. Signed URL ──────────────────────────────────────────────────────────────

async fn create_signed_url(client: &Client) -> Result<Value, Error> {
    let res = client
        .post("/api/v1/signed-url")
        .json(&json!({
            "url": "https://storage.veilpass.app/reports/audit.pdf",
            "permissions": "read",
            "expires_in": 3600,
            "download_limit": 10,
            "one_time": false,
        }))
        .send()
        .await?;

    let data: Value = res.json().await?;
    log("Signed URL", &data);
    Ok(data)
}

// ── 5. Token Generation ────────────────────────────────────────────────────────

async fn generate_token(client: &Client) -> Result<Value, Error> {
    let res = client
        .post("/api/v1/token")
        .json(&json!({
            "subject": "user_abc123",
            "audience": "api.veilpass.app",
            "issuer": "veilpass",
            "expires_in": 86400,
            "claims": { "role": "admin", "region": "us-east" },
        }))
        .send()
        .await?;

    let data: Value = res.json().await?;
    log("Token", &data);
    Ok(data)
}

// ── 6. Verification ─────────────────────────────────────────────────────────────

async fn verify_token(client: &Client, token: &str) -> Result<Value, Error> {
    let res = client
        .post("/api/v1/verify")
        .json(&json!({
            "type": "token",
            "value": token,
        }))
        .send()
        .await?;

    let data: Value = res.json().await?;
    log("Verification", &data);
    Ok(data)
}

// ── Main ────────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let api_base = env_or("VEILPASS_API_URL", "http://localhost:8000");
    let api_key = env_or("VEILPASS_API_KEY", "");

    let mut headers = HeaderMap::new();
    headers.insert("Content-Type", "application/json".parse().unwrap());
    if !api_key.is_empty() {
        headers.insert("X-API-Key", api_key.parse().unwrap());
    }

    let client = Client::builder()
        .default_headers(headers)
        .timeout(Duration::from_secs(30))
        .build()?;

    generate_qr(&client).await?;
    generate_nfc(&client).await?;
    create_signed_link(&client).await?;
    create_signed_url(&client).await?;
    let token = generate_token(&client).await?;
    verify_token(&client, token["token"].as_str().unwrap()).await?;

    println!("\n✅ All API operations completed successfully.");
    Ok(())
}
