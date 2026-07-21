# VeilPass (private-pass) — Architecture Document

> **Project:** Privacy QR + NFC Generator  
> **Organization:** `veillabs`  
> **Repo:** `github.com/veillabs/private-pass`  
> **Status:** Blueprint / Pre-implementation  
> **Date:** 2026-07-22

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Core Modules / Components](#2-core-modules--components)
3. [Security Architecture](#3-security-architecture)
4. [Data Flow](#4-data-flow)
5. [API Design](#5-api-design)
6. [Project Structure](#6-project-structure)
7. [Build & Distribution](#7-build--distribution)
8. [Testing Strategy](#8-testing-strategy)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Technology Stack

### 1.1 Core Language: **Rust**

| Criterion | Decision | Rationale |
|-----------|----------|-----------|
| Crypto/signing logic | **Rust** | Memory safety without GC, zero-cost abstractions, constant-time crypto primitives available (`aws-lc-rs`). |
| Cross-platform compilation | **Rust** | Single codebase → native binaries for Windows, macOS, Linux (x86_64 + aarch64). |
| WASM target | **Rust** | Core library compiles to WASM via `wasm-pack` for web embedding. |
| CLI distribution | **Rust** | Single static binary, no runtime dependency. |
| Library ecosystem | **Rust** | Mature crates for QR (`fast_qr`), NDEF (`ndef-rs`), JWT (`jsonwebtoken`), crypto (`aws-lc-rs`), keyring (`keyring`). |

**Go was considered but rejected** because: Rust's borrow checker prevents the class of memory bugs that plague crypto code, the WASM target is more mature, and the Tauri desktop shell requires Rust.

### 1.2 Desktop Shell: **Tauri v2**

| Criterion | Decision | Rationale |
|-----------|----------|-----------|
| Binary size | **Tauri** (~5 MB) vs Electron (~150 MB) | 30× smaller. |
| Memory usage | **Tauri** (~50 MB) vs Electron (~200 MB) | 4× less RAM. |
| Native APIs | **Tauri** | Direct access to OS keychain, file system, notifications. |
| IPC | **tauri-specta v2** | Type-safe Rust↔TypeScript codegen, no stringly-typed `invoke()`. |
| Updates | **Tauri updater** | Built-in auto-update with signature verification. |

### 1.3 Frontend: **React 19 + TypeScript 6 + Vite 8**

| Layer | Choice | Version |
|-------|--------|---------|
| Framework | React | 19 (stable) |
| Language | TypeScript | ~6.0 |
| Bundler | Vite | 8 |
| Styling | Tailwind CSS | v4 |
| UI primitives | shadcn/ui + Radix | Latest |
| Client state | Zustand | v5 |
| Server/IPC state | TanStack Query | v5 |
| Lint/format | Biome | v2.5 |
| Test runner | Vitest | v4 |

### 1.4 CLI: **clap v4 (derive API)**

- Single binary `vp` (or `veilpass`) with subcommands for headless/CI usage.
- Shell completions generated via `clap_complete`.

### 1.5 Key Rust Crates

| Crate | Purpose | Justification |
|-------|---------|---------------|
| `jsonwebtoken` v11 | JWT creation/validation | 2000+ GitHub stars, AWS-LC-RS backend, supports EdDSA/ES256/RS256. |
| `fast_qr` v0.13 | QR code generation | 6-7× faster than `qrcode`, supports SVG/image/raw matrix output. |
| `ndef-rs` v0.2 | NDEF record parsing/generation | Pure Rust, supports Text/URI/MIME payloads, no_std compatible. |
| `keyring` v4 | OS credential store access | Cross-platform: Windows Credential Manager, macOS Keychain, Linux Secret Service. |
| `clap` v4 | CLI argument parsing | Derive API, environment variable fallback, auto-generated help. |
| `aws-lc-rs` | Cryptographic primitives | AWS-LC (FIPS-ready), constant-time operations, used by `jsonwebtoken`. |
| `serde` / `serde_json` | Serialization | De facto standard, required by JWT. |
| `thiserror` / `anyhow` | Error handling | Structured domain errors + convenient app-level error chaining. |
| `tauri-specta` v2 | Typed IPC | Generates TypeScript bindings from Rust commands at compile time. |
| `uuid` v7 | Unique identifier generation | For claim link IDs, key identifiers. |
| `base64` v0.22 | Base64 encoding | URL-safe encoding for tokens and keys. |
| `chrono` v0.4 | Time handling | For TOTP-like time windows, expiry validation. |
| `zeroize` | Secure memory clearing | Zero out signing keys on drop (prevents memory scraping). |

---

## 2. Core Modules / Components

### 2.1 Module Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     veilpass-core                           │
│  (Library crate — no_std compatible, WASM-compatible)        │
├───────────────┬───────────────┬─────────────────────────────┤
│  nfc::        │  qr::         │  signing::                   │
│  • NdefRecord │  • QrBuilder  │  • KeyPair (Ed25519)         │
│  • TextRecord │  • SvgBuilder │  • HmacKey (HS256/384/512)   │
│  • UriRecord  │  • ImgBuilder │  • SigningKey                │
│  • MimeRecord │  • ECL/Hints  │  • VerificationKey           │
├───────────────┼───────────────┼─────────────────────────────┤
│  tokens::     │  links::      │  crypto::                    │
│  • TimeToken  │  • ClaimLink  │  • KeyGenerator              │
│  • TotpLike   │  • SignedUrl  │  • KeyStore trait            │
│  • Expiring   │  • Verifier   │  • SecureMemory              │
└───────────────┴───────────────┴─────────────────────────────┘
```

### 2.2 Module — `veilpass_core::nfc`

**Purpose:** Generate and parse NDEF (NFC Data Exchange Format) records.

**Key types:**
```rust
/// Represents an NDEF message (one or more records).
pub struct NdefMessage { /* ... */ }

/// A single NDEF record.
pub struct NdefRecord { /* ... */ }

/// Well-known NDEF record types.
pub enum WellKnownType {
    Text { language: String, text: String },
    Uri { uri: String },
    SmartPoster { title: String, uri: String, /* ... */ },
    Mime { content_type: String, data: Vec<u8> },
    External { domain: String, ty: String, data: Vec<u8> },
}

impl NdefMessage {
    /// Encode the message to bytes (ready for NFC tag writing).
    pub fn to_bytes(&self) -> Vec<u8>;

    /// Parse from raw bytes read from an NFC tag.
    pub fn from_bytes(data: &[u8]) -> Result<Self, NdefError>;
}

impl NdefRecord {
    /// Create a URI record (most common for NFC tags).
    pub fn uri(uri: &str) -> Self;

    /// Create a text record.
    pub fn text(text: &str, language: &str) -> Self;

    /// Create a custom MIME record.
    pub fn mime(content_type: &str, data: &[u8]) -> Self;
}
```

### 2.3 Module — `veilpass_core::qr`

**Purpose:** Generate QR codes with configurable error correction, size, and output formats.

**Key types:**
```rust
pub struct QrOptions {
    pub ecl: ErrorCorrectionLevel,   // L, M, Q, H
    pub min_version: Option<u8>,     // 1-40, auto-detect if None
    pub max_version: Option<u8>,
    pub margin: u8,                  // quiet zone modules
}

pub enum QrOutput {
    Svg(String),
    Png(Vec<u8>),
    RawMatrix(Vec<Vec<bool>>),
    Terminal(String),
}

pub fn generate_qr(content: &str, opts: &QrOptions) -> Result<QrOutput, QrError>;
```

**Implementation:** Wraps `fast_qr` with our own options struct and error types. Default ECL is **H** (highest, ~30% redundancy) since these QR codes will be scanned from screens and stickers where damage is likely.

### 2.4 Module — `veilpass_core::signing`

**Purpose:** Cryptographic key management and digital signing.

**Key types:**
```rust
/// Ed25519 key pair — the PRIMARY signing algorithm.
pub struct SigningKey {
    inner: ed25519_dalek::SigningKey,
}

pub struct VerificationKey {
    inner: ed25519_dalek::VerifyingKey,
}

/// HMAC-SHA256 symmetric key (for shared-secret scenarios).
pub struct HmacKey {
    inner: [u8; 32],
}

impl SigningKey {
    pub fn generate() -> Self;
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, CryptoError>;
    pub fn to_bytes(&self) -> Vec<u8>;   // for secure storage
    pub fn sign(&self, data: &[u8]) -> Signature;
    pub fn verification_key(&self) -> VerificationKey;
}

impl VerificationKey {
    pub fn verify(&self, data: &[u8], signature: &Signature) -> Result<(), CryptoError>;
    pub fn to_bytes(&self) -> Vec<u8>;
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, CryptoError>;
}
```

**Algorithm choice rationale:**
- **Ed25519** (Edwards-curve Digital Signature Algorithm) is the PRIMARY signing algorithm.
  - Compact signatures (64 bytes).
  - Fast verification (~6.5 µs with `aws-lc-rs`).
  - Deterministic (no RNG failures, unlike ECDSA).
  - Resistant to side-channel attacks.
- **HMAC-SHA256** is the SECONDARY option for shared-secret scenarios:
  - Simpler key distribution (shared secret instead of PKI).
  - Used for HS256 JWTs when the user wants symmetric signing.
- **RSA** is NOT supported by default to keep binary size small and avoid algorithm confusion attacks.

### 2.5 Module — `veilpass_core::tokens`

**Purpose:** Generate and verify time-limited tokens.

**Token types:**

| Token Type | Description | Use Case |
|-----------|-------------|----------|
| `BearerToken` | JWT with `exp`, `iat`, `jti`, custom claims | API authentication, resource access |
| `TOTPLike` | Time-based window token (similar to TOTP but using HMAC-SHA256) | Short-lived verification codes |
| `ExpiringClaim` | Signed token with absolute expiry, one-time-use flag | Claim links, password resets |

**Key types:**
```rust
pub struct TokenConfig {
    pub algorithm: Algorithm,         // Ed25519 or HS256
    pub issuer: String,
    pub audience: Option<String>,
    pub default_ttl: Duration,        // default: 24 hours
    pub max_ttl: Duration,            // default: 30 days
    pub clock_skew_leeway: Duration,  // default: 30 seconds
}

pub struct BearerToken {
    pub claims: TokenClaims,
    pub raw: String,                  // the JWT string
}

#[derive(Serialize, Deserialize)]
pub struct TokenClaims {
    pub sub: String,           // subject (e.g., resource identifier)
    pub iss: String,           // issuer
    pub aud: Option<String>,   // audience
    pub exp: usize,            // expiry (Unix timestamp)
    pub iat: usize,            // issued at
    pub nbf: Option<usize>,    // not before
    pub jti: Option<String>,   // unique token ID (for revocation)
    pub scope: Option<Vec<String>>,  // permissions
    pub custom: Option<serde_json::Value>, // extensible
}

impl BearerToken {
    pub fn issue(
        signing_key: &SigningKey,
        claims: TokenClaims,
        config: &TokenConfig,
    ) -> Result<Self, TokenError>;

    pub fn verify(
        token_str: &str,
        verification_key: &VerificationKey,
        config: &TokenConfig,
    ) -> Result<TokenClaims, TokenError>;
}
```

### 2.6 Module — `veilpass_core::links`

**Purpose:** Generate cryptographically signed claim links and signed URLs.

**Architecture:**
A claim link embeds a signed JWT in a URL. The URL format is:

```
https://claim.veilpass.app/c/{token}
```

Where `{token}` is a URL-safe Base64-encoded JWT containing:
- `sub` — the resource being claimed
- `exp` — expiry timestamp
- `jti` — unique ID (prevents replay if combined with server-side state)
- `r` — random nonce (entropy for unguessability)
- `sig` — Ed25519 signature over the claims (or JWT wrapper)

**Key types:**
```rust
pub struct ClaimLink {
    pub url: String,              // full claim URL
    pub token: String,            // the embedded token (JWT)
    pub metadata: ClaimMetadata,
}

pub struct ClaimMetadata {
    pub resource: String,
    pub expires_at: chrono::DateTime<chrono::Utc>,
    pub one_time: bool,
    pub max_uses: Option<u32>,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

pub struct SignedUrl {
    pub url: String,              // original URL + signature query params
    pub signature_params: SignedUrlParams,
}

pub struct SignedUrlParams {
    pub expires: chrono::DateTime<chrono::Utc>,
    pub signature: String,        // Base64-encoded Ed25519 signature
    pub key_id: String,           // identifies which key signed it
}

impl ClaimLink {
    pub fn generate(
        resource: &str,
        signing_key: &SigningKey,
        config: &TokenConfig,
        one_time: bool,
    ) -> Result<Self, LinkError>;

    pub fn verify(
        url: &str,
        verification_key: &VerificationKey,
        config: &TokenConfig,
    ) -> Result<ClaimMetadata, LinkError>;
}

impl SignedUrl {
    pub fn sign(
        base_url: &str,
        signing_key: &SigningKey,
        ttl: Duration,
    ) -> Result<Self, LinkError>;

    pub fn verify(
        signed_url: &str,
        verification_key: &VerificationKey,
    ) -> Result<String, LinkError>;  // returns the original URL
}
```

---

## 3. Security Architecture

### 3.1 Cryptographic Primitives (Summary)

| Operation | Algorithm | Crate | Key Size |
|-----------|-----------|-------|----------|
| Digital signatures | Ed25519 | `ed25519-dalek` via `aws-lc-rs` | 32 bytes secret + 32 bytes public |
| Symmetric signing | HMAC-SHA256 | `aws-lc-rs` | 32 bytes (256 bits) |
| JWT | HS256 / EdDSA | `jsonwebtoken` | Per algorithm |
| Key derivation | HKDF-SHA256 | `aws-lc-rs` | N/A |
| Random generation | `getrandom` / OS CSPRNG | `getrandom` | N/A |
| Secure memory | `zeroize` on drop | `zeroize` | N/A |
| Token ID (jti) | UUID v7 | `uuid` | 128 bits |

### 3.2 Key Management

**Key hierarchy:**

```
[Master Signing Key] (Ed25519 — stored in OS keychain)
        │
        ├── [Derived Sub-Key 1] (HKDF → specific purpose, e.g., "claim-links")
        ├── [Derived Sub-Key 2] (HKDF → specific purpose, e.g., "signed-urls")
        └── [Derived Sub-Key 3] (HKDF → specific purpose, e.g., "time-tokens")
```

- The **master key** is stored in the OS credential store (Windows Credential Manager, macOS Keychain, Linux Secret Service) via the `keyring` crate.
- **Sub-keys** are derived via HKDF-SHA256 with a domain separation tag. They are computed at startup and held in `zeroize`-protected memory.
- **Key ID** (`kid`) is the first 8 bytes of the SHA-256 hash of the public key, encoded as hex.
- Users can **export/import** keys as encrypted bundles (AES-256-GCM with a passphrase).

```rust
pub struct KeyManager {
    master: Option<Zeroizing<SigningKey>>,
    sub_keys: HashMap<String, Zeroizing<SigningKey>>,
}

impl KeyManager {
    /// Load master key from OS keychain, or generate if none exists.
    pub fn initialize(service_name: &str) -> Result<Self, KeyError>;

    /// Derive a purpose-specific sub-key.
    pub fn derive_key(&self, purpose: &str) -> Result<SigningKey, KeyError>;

    /// Export master key as encrypted bundle (passphrase-protected).
    pub fn export_master(&self, passphrase: &str) -> Result<Vec<u8>, KeyError>;

    /// Import master key from encrypted bundle.
    pub fn import_master(data: &[u8], passphrase: &str) -> Result<Self, KeyError>;
}
```

### 3.3 Token Tamper Prevention

1. **Signature binding:** Every token/JWT is Ed25519-signed. The signature covers the entire payload (headers + claims).
2. **Algorithm lockdown:** The verifier specifies the exact allowed algorithm (never reads `alg` from the token header). This prevents algorithm confusion attacks.
3. **Expiry validation:** The `exp` claim is checked on every verification. A configurable leeway (default 30s) accounts for clock skew.
4. **Not-before validation:** Optional `nbf` claim for tokens that should not be valid before a certain time.
5. **Token ID (jti):** Each token gets a unique UUID v7. For one-time tokens, the verifier MUST check that the `jti` has not been used before (requires server-side state).
6. **Replay prevention:** The `jti` + `iat` combination prevents replay within the validity window.

### 3.4 Secure Defaults

| Setting | Default | Rationale |
|---------|---------|-----------|
| Signing algorithm | Ed25519 | Strongest default, compact signatures |
| QR error correction | H (~30%) | Maximizes scan reliability |
| Token TTL | 24 hours | Short enough to limit exposure, long enough for usability |
| Max TTL | 30 days | Prevents accidentally creating perpetual tokens |
| Clock skew leeway | 30 seconds | Standard for distributed systems |
| Key size | 256-bit (Ed25519) | NIST-compliant, post-quantum safe enough for current threats |

### 3.5 Threat Model

| Threat | Mitigation |
|--------|-----------|
| Token forgery | Ed25519 signature verification |
| Token replay | `jti` uniqueness + optional server-side state |
| Token theft (interception) | TLS for transmission, short TTL limits window |
| Key extraction from disk | OS keychain encryption + `zeroize` on drop |
| Algorithm confusion | Verifier specifies algorithm, not token |
| Timing side-channel | Constant-time comparison via `aws-lc-rs` |
| Brute-force via QR | QR content is signed; forgery would require valid signature |
| Clipboard/injection | Input validation on all user-provided fields |

---

## 4. Data Flow

### 4.1 Primary Flow: Generate QR + NFC

```
User Input (Web UI / CLI)
    │
    ▼
┌─────────────────────────────────┐
│  veilpass-core::links           │
│  Generate ClaimLink / SignedUrl │
│  Returns: url + metadata        │
└──────────────┬──────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐  ┌──────────────┐
│ qr::generate │  │ nfc::NdefMsg │
│ (URL→QR)     │  │ (URL→NDEF)   │
│ Output: PNG/ │  │ Output: bytes│
│ SVG/Matrix   │  │ (for NFC tag)│
└──────────────┘  └──────────────┘
       │               │
       ▼               ▼
  [QR Image]      [NFC Binary]
  (display/       (write to
   download/       NFC tag/
   print)          share)
```

### 4.2 Claim Link Verification Flow

```
User scans QR / clicks link
    │
    ▼
GET https://claim.veilpass.app/c/{token}
    │
    ▼
┌────────────────────────────────────┐
│  Verification Service              │
│  (deployed separately, or local)   │
│  1. Parse JWT from URL             │
│  2. Verify Ed25519 signature       │
│  3. Check exp, nbf, iat            │
│  4. Check jti (if one-time)        │
│  5. Return: { resource, valid }    │
└────────────────────────────────────┘
    │
    ▼
[Resource granted / Denied]
```

### 4.3 Key Lifecycle Flow

```
First Run:
  │
  ├─ Check OS keychain for existing key
  ├─ If missing: generate Ed25519 key → store in keychain
  └─ Derive sub-keys for each purpose (claims, URLs, tokens)

Subsequent Runs:
  │
  ├─ Load master key from keychain
  ├─ Derive sub-keys (deterministic from master + purpose tag)
  └─ Ready for signing operations

Key Export:
  │
  ├─ User provides passphrase
  ├─ Master key encrypted with AES-256-GCM (key derived via Argon2id)
  └─ Encrypted bundle saved to file

Key Import:
  │
  ├─ User provides passphrase + bundle file
  ├─ Argon2id → AES-256-GCM decryption
  ├─ Key stored in OS keychain
  └─ Ready for use
```

### 4.4 QR Encodes Link (Composition)

The most common use case: a QR code encodes an NFC URL that points to a secure claim link.

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claim Link  │────▶│  NFC NDEF Record │────▶│  QR Code Image  │
│  (signed JWT │     │  (URI: claim URL)│     │  (encodes NFC   │
│   embedded)  │     │                  │     │   content URL)  │
└──────────────┘     └──────────────────┘     └─────────────────┘
```

This allows three distribution channels from a single generation step:
1. **QR code** — printed on stickers, displayed on screens
2. **NFC tag** — tapped with a phone
3. **Direct link** — shared via messaging apps

---

## 5. API Design

### 5.1 Rust Library API (`veilpass-core`)

#### 5.1.1 QR Generation

```rust
use veilpass_core::qr::{self, QrOptions, QrOutput, ErrorCorrectionLevel};

// Simple generation (defaults: ECL=H, PNG output)
let png: Vec<u8> = qr::generate_png("https://example.com")?;

// Advanced options
let output = qr::generate(
    "https://example.com/claim/abc123",
    &QrOptions {
        ecl: ErrorCorrectionLevel::High,
        margin: 4,
        output_format: qr::OutputFormat::Svg,
        width: 512,
        ..Default::default()
    },
)?;

match output {
    QrOutput::Svg(svg) => fs::write("qr.svg", svg)?,
    QrOutput::Png(png) => fs::write("qr.png", png)?,
    QrOutput::RawMatrix(m) => { /* custom rendering */ }
    _ => {}
}
```

#### 5.1.2 NFC NDEF Generation

```rust
use veilpass_core::nfc::{NdefMessage, NdefRecord};

// Create a URI NDEF record
let record = NdefRecord::uri("https://claim.veilpass.app/c/abc123");
let message = NdefMessage::from(vec![record]);
let nfc_bytes: Vec<u8> = message.to_bytes()?;  // write this to NFC tag

// Create a Smart Poster (title + URI)
let poster = NdefMessage::smart_poster(
    "Claim Your Reward",
    "https://claim.veilpass.app/c/abc123",
)?;
```

#### 5.1.3 Claim Link Generation

```rust
use veilpass_core::links::ClaimLink;
use veilpass_core::signing::SigningKey;
use veilpass_core::tokens::TokenConfig;
use std::time::Duration;

let key = SigningKey::generate();

let link = ClaimLink::generate(
    "resource://tickets/vip-001",
    &key,
    &TokenConfig::default(),
    true, // one-time use
)?;

println!("{}", link.url);
// https://claim.veilpass.app/c/eyJhbGciOiJFZERTQSJ9...
```

#### 5.1.4 Signed URL Generation

```rust
use veilpass_core::links::SignedUrl;
use veilpass_core::signing::SigningKey;
use std::time::Duration;

let key = SigningKey::generate();

let signed = SignedUrl::sign(
    "https://api.example.com/files/secret.pdf",
    &key,
    Duration::from_secs(3600), // 1 hour TTL
)?;

println!("{}", signed.url);
// https://api.example.com/files/secret.pdf?expires=...&sig=...&kid=...
```

#### 5.1.5 Time-Limited Token

```rust
use veilpass_core::tokens::{BearerToken, TokenClaims, TokenConfig};
use veilpass_core::signing::SigningKey;
use std::time::Duration;

let key = SigningKey::generate();

let token = BearerToken::issue(
    &key,
    TokenClaims::new("user-001")
        .with_ttl(Duration::from_secs(86400))
        .with_scope(vec!["read:tickets".into()]),
    &TokenConfig::default(),
)?;

println!("{}", token.raw);
// eyJhbGciOiJFZERTQSJ9.eyJzdWIiOiJ1c2VyLTAwMSIs...

// Later, verify:
let claims = BearerToken::verify(&token.raw, &key.verification_key(), &TokenConfig::default())?;
assert_eq!(claims.sub, "user-001");
```

### 5.2 CLI API (`vp` command)

```
VeilPass — Privacy QR & NFC Generator

USAGE:
    vp [OPTIONS] <COMMAND>

COMMANDS:
    qr          Generate QR codes
    nfc         Generate NFC NDEF payloads
    link        Generate secure claim links
    sign        Sign a URL or message
    token       Generate time-limited tokens
    key         Manage signing keys
    verify      Verify a token, link, or signature
    complete    Generate shell completions

OPTIONS:
    -o, --output <PATH>    Output directory [default: .]
    -f, --format <FMT>     Output format [possible: png, svg, terminal, raw]
    -q, --quiet            Suppress non-essential output
    -v, --verbose          Increase verbosity
    --json                 Output as JSON (machine-readable)
    -h, --help             Print help
    -V, --version          Print version

EXAMPLES:
    # Generate a QR code from a URL
    vp qr "https://example.com"

    # Generate a QR code with custom options
    vp qr "https://example.com" -o output.svg -f svg --ecl H --width 1024

    # Generate an NFC NDEF payload
    vp nfc uri "https://example.com" -o tag.bin

    # Generate a secure claim link
    vp link create "resource://tickets/vip-001" --ttl 24h --one-time

    # Sign a URL (produces signed URL with expiry)
    vp sign url "https://api.example.com/files/doc.pdf" --ttl 1h

    # Generate a time-limited bearer token
    vp token issue --sub "user-001" --ttl 7d --scope "read:tickets"

    # Verify a token
    vp verify token "eyJhbGciOiJFZERTQSJ9..."

    # Manage keys
    vp key init                    # Generate and store a new key
    vp key list                    # List available keys
    vp key export ./backup.key     # Export encrypted key
    vp key import ./backup.key     # Import key

    # Verify a claim link
    vp verify link "https://claim.veilpass.app/c/eyJhbGci..."

    # Generate shell completions
    vp complete bash > ~/.bash_completion.d/veilpass
```

### 5.3 Tauri IPC Commands (Desktop App)

The desktop app exposes the same functionality via typed IPC commands:

```typescript
// Generated by tauri-specta — fully typed

// QR
commands.generateQr(options: {
  content: string;
  format: "png" | "svg" | "raw";
  ecl?: "L" | "M" | "Q" | "H";
  width?: number;
}): Promise<QrResult>;

// NFC
commands.generateNdef(options: {
  recordType: "uri" | "text" | "smartPoster";
  content: string;
  title?: string;
}): Promise<NdefResult>;

// Links
commands.createClaimLink(options: {
  resource: string;
  ttl?: string;
  oneTime?: boolean;
}): Promise<ClaimLinkResult>;

commands.verifyClaimLink(url: string): Promise<ClaimVerificationResult>;

// Signed URLs
commands.signUrl(options: {
  url: string;
  ttl?: string;
}): Promise<SignedUrlResult>;

// Tokens
commands.issueToken(options: {
  subject: string;
  ttl?: string;
  scope?: string[];
  audience?: string;
}): Promise<TokenResult>;

commands.verifyToken(token: string): Promise<TokenVerificationResult>;

// Key management
commands.initializeKey(): Promise<void>;
commands.getKeyInfo(): Promise<KeyInfo>;
commands.exportKey(passphrase: string): Promise<number[]>; // encrypted bytes
commands.importKey(data: number[], passphrase: string): Promise<void>;
```

### 5.4 API Types (Shared)

```typescript
// Shared types passed between Rust ↔ TypeScript IPC

interface QrResult {
  data: number[];        // PNG bytes or SVG XML string
  format: "png" | "svg";
  size: { width: number; height: number };
  version: number;
}

interface NdefResult {
  bytes: number[];       // Raw NDEF bytes for tag writing
  records: NdefRecordInfo[];
}

interface ClaimLinkResult {
  url: string;
  token: string;
  metadata: {
    resource: string;
    expiresAt: string;   // ISO 8601
    oneTime: boolean;
  };
}

interface TokenResult {
  token: string;
  claims: {
    subject: string;
    issuer: string;
    issuedAt: string;
    expiresAt: string;
    scope?: string[];
  };
}

interface KeyInfo {
  algorithm: "Ed25519" | "HS256";
  publicKey: string;     // hex-encoded
  keyId: string;         // 8-byte hex prefix
  createdAt: string;
  subKeys: string[];     // purpose tags
}
```

---

## 6. Project Structure

```
private-pass/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Build + test + lint on PR/push
│   │   ├── release.yml               # Build binaries, publish to GitHub Releases
│   │   ├── publish-crates.yml        # Publish crates to crates.io
│   │   └── publish-npm.yml           # Publish WASM package to npm
│   ├── CODEOWNERS
│   └── dependabot.yml
│
├── crates/
│   ├── veilpass-core/               # Core library (no_std friendly)
│   │   ├── src/
│   │   │   ├── lib.rs               # Re-exports, pub mod declarations
│   │   │   ├── error.rs             # Unified error types
│   │   │   ├── crypto/
│   │   │   │   ├── mod.rs
│   │   │   │   ├── keygen.rs        # Key generation
│   │   │   │   ├── keyring.rs       # OS keychain integration
│   │   │   │   └── secure_mem.rs    # zeroize wrappers
│   │   │   ├── signing/
│   │   │   │   ├── mod.rs
│   │   │   │   ├── ed25519.rs       # Ed25519 sign/verify
│   │   │   │   ├── hmac.rs          # HMAC sign/verify
│   │   │   │   └── types.rs         # SigningKey, VerificationKey, etc.
│   │   │   ├── tokens/
│   │   │   │   ├── mod.rs
│   │   │   │   ├── bearer.rs        # BearerToken (JWT)
│   │   │   │   ├── expiry.rs        # ExpiringClaim
│   │   │   │   └── totp_like.rs     # Time-window tokens
│   │   │   ├── links/
│   │   │   │   ├── mod.rs
│   │   │   │   ├── claim.rs         # ClaimLink
│   │   │   │   └── signed_url.rs    # SignedUrl
│   │   │   ├── qr/
│   │   │   │   ├── mod.rs
│   │   │   │   ├── builder.rs       # QR generation (wraps fast_qr)
│   │   │   │   └── types.rs         # QrOptions, QrOutput
│   │   │   └── nfc/
│   │   │       ├── mod.rs
│   │   │       ├── ndef.rs          # NDEF message building (wraps ndef-rs)
│   │   │       ├── records.rs       # Record type helpers
│   │   │       └── types.rs         # NdefMessage, NdefRecord
│   │   ├── tests/
│   │   │   ├── crypto_vectors.rs    # Test vectors (Wycheproof, etc.)
│   │   │   ├── qr_roundtrip.rs      # QR encode → decode → verify
│   │   │   ├── nfc_roundtrip.rs     # NFC encode → decode → verify
│   │   │   ├── token_validation.rs  # Token issue → verify → reject
│   │   │   └── link_verification.rs # Link generation → verification
│   │   ├── benches/
│   │   │   ├── signing.rs
│   │   │   ├── qr_generation.rs
│   │   │   └── token_operations.rs
│   │   ├── Cargo.toml
│   │   └── README.md
│   │
│   ├── veilpass-cli/               # CLI binary
│   │   ├── src/
│   │   │   ├── main.rs             # Entrypoint, clap parser
│   │   │   ├── commands/
│   │   │   │   ├── mod.rs
│   │   │   │   ├── qr_cmd.rs
│   │   │   │   ├── nfc_cmd.rs
│   │   │   │   ├── link_cmd.rs
│   │   │   │   ├── sign_cmd.rs
│   │   │   │   ├── token_cmd.rs
│   │   │   │   ├── key_cmd.rs
│   │   │   │   └── verify_cmd.rs
│   │   │   ├── output.rs           # Format output (terminal, JSON, file)
│   │   │   └── config.rs           # Config file handling (~/.veilpass/config.toml)
│   │   ├── tests/
│   │   │   ├── cli_integration.rs
│   │   │   └── snapshots/          # insta snapshot tests for CLI output
│   │   ├── Cargo.toml
│   │   └── README.md
│   │
│   └── veilpass-tauri/            # Tauri desktop backend (Rust)
│       ├── src/
│       │   ├── lib.rs              # Plugin wiring, specta builder
│       │   ├── main.rs             # tauri::Builder setup
│       │   ├── commands/
│       │   │   ├── mod.rs
│       │   │   ├── qr_commands.rs
│       │   │   ├── nfc_commands.rs
│       │   │   ├── link_commands.rs
│       │   │   ├── sign_commands.rs
│       │   │   ├── token_commands.rs
│       │   │   └── key_commands.rs
│       │   ├── error.rs            # AppError: serializable tagged errors
│       │   ├── state.rs            # AppState: holds KeyManager, config
│       │   └── bindings.rs         # specta type collection
│       ├── capabilities/
│       │   ├── default.json
│       │   ├── desktop.json
│       │   └── keyring.json
│       ├── icons/
│       ├── Cargo.toml
│       └── tauri.conf.json
│
├── src/                            # Frontend (React + TypeScript)
│   ├── main.tsx                    # Entrypoint
│   ├── App.tsx                     # Root component
│   ├── bindings.ts                 # GENERATED by tauri-specta
│   ├── routes.tsx                  # React Router config
│   │
│   ├── lib/
│   │   ├── ipc/
│   │   │   ├── index.ts           # Re-exports commands, queryKeys
│   │   │   └── unwrap.ts          # Result unwrapping helpers
│   │   ├── hooks/
│   │   │   ├── useQrGeneration.ts
│   │   │   ├── useNfcGeneration.ts
│   │   │   ├── useLinkGeneration.ts
│   │   │   ├── useTokenGeneration.ts
│   │   │   └── useKeyManagement.ts
│   │   └── utils/
│   │       ├── download.ts
│   │       └── format.ts
│   │
│   ├── features/
│   │   ├── qr/
│   │   │   ├── QrGenerator.tsx      # QR generation form
│   │   │   ├── QrPreview.tsx        # QR code preview
│   │   │   └── QrOptionsPanel.tsx   # ECL, size, margin controls
│   │   ├── nfc/
│   │   │   ├── NfcGenerator.tsx
│   │   │   └── NfcPreview.tsx
│   │   ├── links/
│   │   │   ├── ClaimLinkForm.tsx
│   │   │   └── ClaimLinkResult.tsx
│   │   ├── tokens/
│   │   │   ├── TokenForm.tsx
│   │   │   └── TokenDisplay.tsx
│   │   ├── keys/
│   │   │   ├── KeyManager.tsx
│   │   │   ├── KeyExportDialog.tsx
│   │   │   └── KeyImportDialog.tsx
│   │   └── verify/
│   │       ├── Verifier.tsx
│   │       └── VerificationResult.tsx
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── ui/                     # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   └── shared/
│   │       ├── CopyButton.tsx
│   │       ├── DownloadButton.tsx
│   │       └── OutputPreview.tsx
│   │
│   ├── stores/
│   │   ├── uiStore.ts              # Zustand: UI state (panels, modals)
│   │   └── settingsStore.ts        # Zustand + persist: user prefs
│   │
│   └── styles/
│       └── globals.css
│
├── package.json                    # Root: workspace config, dev deps
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── biome.json                      # Lint/format config
├── .gitignore
├── LICENSE                         # MIT
├── README.md
├── CONTRIBUTING.md
└── rust-toolchain.toml             # Pinned Rust version
```

---

## 7. Build & Distribution

### 7.1 Distribution Targets

| Artifact | Format | Platform(s) | Method |
|----------|--------|-------------|--------|
| **CLI binary** | Static binary | Windows (.exe), macOS, Linux | GitHub Releases, Homebrew (macOS), Scoop (Windows) |
| **Desktop app** | DMG/EXE/AppImage | Windows, macOS, Linux | Tauri build → GitHub Releases, auto-update |
| **Library** | `cargo` crate | All (Rust) | crates.io (`veilpass-core`) |
| **WASM package** | `npm` package | Web, Node.js | npm (`@veillabs/veilpass`) |
| **Docker image** | Docker | Linux | ghcr.io/veillabs/veilpass |

### 7.2 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml — runs on every PR and push to main
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: cargo fmt --check
      - run: cargo clippy --all-targets -- -D warnings
      - run: biome check .

  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - run: cargo test --workspace
      - run: cargo test --workspace --release  # crypto benchmarks

  security:
    steps:
      - run: cargo audit       # Known vulnerability scan
      - run: cargo deny check  # License compliance + bans
      - run: cargo udeps       # Unused dependency detection

  wasm:
    steps:
      - run: wasm-pack build crates/veilpass-core --target web --release
      - run: wasm-pack test --node crates/veilpass-core

# .github/workflows/release.yml — on tag push
jobs:
  build-cli:
    strategy:
      matrix:
        target:
          - x86_64-unknown-linux-gnu
          - x86_64-apple-darwin
          - aarch64-apple-darwin
          - x86_64-pc-windows-msvc
    steps:
      - run: cargo build --release --target ${{ matrix.target }}
      - run: cargo test --target ${{ matrix.target }}
      - upload: release artifacts

  build-desktop:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - run: npm ci
      - run: pnpm tauri build
      - upload: .dmg/.exe/.AppImage, .msi

  publish-crates:
    steps:
      - run: cargo publish -p veilpass-core
      - run: cargo publish -p veilpass-cli

  publish-npm:
    steps:
      - run: wasm-pack build crates/veilpass-core --target web
      - run: npm publish --access public

  publish-docker:
    steps:
      - run: docker build -t ghcr.io/veillabs/veilpass:latest .
      - run: docker push ghcr.io/veillabs/veilpass:latest
```

### 7.3 Homebrew Tap

A Homebrew formula for macOS:

```ruby
class Veilpass < Formula
  desc "Privacy QR + NFC Generator"
  homepage "https://github.com/veillabs/private-pass"
  version "0.1.0"
  
  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/veillabs/private-pass/releases/download/v0.1.0/veilpass-aarch64-apple-darwin.tar.gz"
      sha256 "..."
    else
      url "https://github.com/veillabs/private-pass/releases/download/v0.1.0/veilpass-x86_64-apple-darwin.tar.gz"
      sha256 "..."
    end
  end

  def install
    bin.install "vp"
    man1.install "man/vp.1"
  end
end
```

### 7.4 Docker Image

```dockerfile
FROM rust:1.85-alpine AS build
WORKDIR /build
COPY crates/veilpass-core crates/veilpass-core
COPY crates/veilpass-cli crates/veilpass-cli
COPY Cargo.toml Cargo.lock ./
RUN cargo build --release -p veilpass-cli

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=build /build/target/release/vp /usr/local/bin/vp
ENTRYPOINT ["vp"]
```

### 7.5 WASM / npm Package

```bash
# Build WASM (called during CI)
wasm-pack build crates/veilpass-core \
  --target web \
  --out-dir ../../pkg \
  --release

# npm package: @veillabs/veilpass
npm publish pkg/
```

Usage from TypeScript/JavaScript:

```typescript
import init, { generateQr, createClaimLink } from "@veillabs/veilpass";

await init(); // Load WASM
const qr = generateQr("https://example.com", { ecl: "H" });
const link = createClaimLink("resource://tickets/001");
```

---

## 8. Testing Strategy

### 8.1 Test Levels

| Level | Scope | Tools | What We Test |
|-------|-------|-------|-------------|
| **Unit** | Individual functions | `cargo test` (Rust), `vitest` (TS) | Pure logic, input validation, edge cases |
| **Crypto vectors** | Sign/verify correctness | Wycheproof test vectors | Ed25519/HMAC against known-good signatures |
| **Round-trip** | Encode → decode → verify | `#[cfg(test)]` modules | QR encode → decode, NFC build → parse, JWT issue → verify |
| **Integration** | Cross-module flows | `cargo test --test` | CLI end-to-end flows, IPC command execution |
| **Security** | Vulnerability scanning | `cargo audit`, `cargo deny`, `trivy` | Dependency CVEs, license compliance |
| **Snapshot** | CLI output stability | `insta` (Rust), `vitest` + snapshot (TS) | CLI --help output, JSON output format |
| **Fuzz** | Random input safety | `cargo fuzz` | Token parsing, URL parsing, NDEF parsing |

### 8.2 Unit Test Examples

```rust
// tests/qr_roundtrip.rs
#[test]
fn test_qr_encode_decode_roundtrip() {
    let content = "https://claim.veilpass.app/c/test-123";
    let qr = generate_qr(content, &QrOptions::default()).unwrap();
    
    // Verify the QR decodes back to the original content
    let decoded = decode_qr(&qr.to_png().unwrap()).unwrap();
    assert_eq!(decoded, content);
}

// tests/token_validation.rs
#[test]
fn test_expired_token_rejected() {
    let key = SigningKey::generate();
    let token = BearerToken::issue(
        &key,
        TokenClaims::new("test")
            .with_ttl(Duration::from_secs(0)), // expired immediately
        &TokenConfig::default(),
    ).unwrap();
    
    // Give it a moment to expire
    std::thread::sleep(Duration::from_millis(10));
    
    let result = BearerToken::verify(
        &token.raw,
        &key.verification_key(),
        &TokenConfig::default(),
    );
    assert!(matches!(result, Err(TokenError::Expired)));
}

// tests/token_validation.rs
#[test]
fn test_tampered_token_rejected() {
    let key = SigningKey::generate();
    let token = BearerToken::issue(
        &key,
        TokenClaims::new("test"),
        &TokenConfig::default(),
    ).unwrap();
    
    // Tamper with the payload
    let mut parts: Vec<&str> = token.raw.split('.').collect();
    parts[1] = base64::encode("{\"sub\":\"hacker\"}"); // tampered claims
    let tampered = parts.join(".");
    
    let result = BearerToken::verify(
        &tampered,
        &key.verification_key(),
        &TokenConfig::default(),
    );
    assert!(matches!(result, Err(TokenError::InvalidSignature)));
}

// tests/crypto_vectors.rs
#[test]
fn test_ed25519_wycheproof_vectors() {
    // Load Wycheproof test vectors for Ed25519 and verify
    let vectors = include_json!("vectors/ed25519_test.json");
    for case in vectors.test_groups {
        for test in case.tests {
            let key = VerificationKey::from_bytes(&test.public_key).unwrap();
            let result = key.verify(&test.message, &test.signature);
            if test.expected == "valid" {
                assert!(result.is_ok(), "Test case {} should be valid", test.tc_id);
            } else {
                assert!(result.is_err(), "Test case {} should be invalid", test.tc_id);
            }
        }
    }
}
```

### 8.3 Security-Specific Tests

```rust
// Test constant-time comparison
#[test]
fn test_constant_time_verify() {
    // Ensure signature verification takes approximately the same time
    // regardless of where the comparison fails
    let key = SigningKey::generate();
    let valid_sig = key.sign(b"test data");
    let invalid_sigs = generate_near_matches(&valid_sig);
    
    let start = Instant::now();
    for sig in &invalid_sigs {
        let _ = key.verification_key().verify(b"test data", sig);
    }
    let total_time = start.elapsed();
    
    // Variance should be minimal (within 5%)
    // (Implementation uses constant-time verification from aws-lc-rs)
}

// Test algorithm confusion prevention
#[test]
fn test_algorithm_confusion_rejected() {
    let hmac_key = HmacKey::generate();
    let signing_key = SigningKey::generate();
    
    // Create a token with HMAC but try to verify with Ed25519
    let hmac_token = BearerToken::issue(
        &hmac_key,
        TokenClaims::new("test"),
        &TokenConfig::default(),
    ).unwrap();
    
    // Verifier specifies Ed25519 only — should reject HMAC token
    let config = TokenConfig {
        algorithm: Algorithm::EdDSA, // Only allow EdDSA
        ..Default::default()
    };
    
    let result = BearerToken::verify(
        &hmac_token.raw,
        &signing_key.verification_key(),
        &config,
    );
    assert!(result.is_err());
}
```

### 8.4 Fuzz Testing

```rust
// fuzz_targets/token_parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    // Fuzz token parsing — should never panic
    if let Ok(s) = std::str::from_utf8(data) {
        let _ = BearerToken::verify(s, &test_key(), &TokenConfig::default());
    }
});
```

### 8.5 Frontend Tests

```typescript
// src/features/qr/__tests__/QrGenerator.test.tsx
import { render, screen } from "@testing-library/react";
import { QrGenerator } from "../QrGenerator";

test("renders QR generation form", () => {
  render(<QrGenerator />);
  expect(screen.getByText("Generate QR Code")).toBeInTheDocument();
  expect(screen.getByPlaceholderText("Enter URL or text...")).toBeInTheDocument();
});

test("shows preview after generation", async () => {
  const mockGenerate = vi.fn().mockResolvedValue({
    data: [1, 2, 3],
    format: "png",
    size: { width: 512, height: 512 },
    version: 10,
  });
  
  render(<QrGenerator onGenerate={mockGenerate} />);
  await userEvent.type(screen.getByPlaceholderText("Enter URL or text..."), "https://example.com");
  await userEvent.click(screen.getByText("Generate"));
  
  expect(await screen.findByTestId("qr-preview")).toBeInTheDocument();
});
```

### 8.6 End-to-End Test Scenarios

1. **Generate QR → Scan → Verify link**
   - CLI: `vp qr "https://claim.veilpass.app/c/TOKEN" → output.png`
   - Decode QR with `zxing` or similar → verify URL matches
   
2. **Issue token → Verify → Tamper → Reject**
   - `vp token issue --sub "user" --ttl 1h` → get token
   - `vp verify token TOKEN` → succeeds
   - Modify one character in token → verify fails
   
3. **Key export → Import → Sign → Verify**
   - `vp key export backup.key --passphrase "test"`
   - Remove original key → `vp key import backup.key --passphrase "test"`
   - Sign with imported key → verify passes

4. **Key persistence across app restarts (Tauri)**
   - Initialize key in desktop app
   - Restart app
   - Key should still be available (from OS keychain)

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Cargo workspace with `veilpass-core`, `veilpass-cli`, `veilpass-tauri`
- [ ] Implement `veilpass_core::crypto` — key generation, Ed25519 sign/verify, HMAC
- [ ] Implement `veilpass_core::signing` — SigningKey, VerificationKey, HmacKey
- [ ] Implement `veilpass_core::tokens` — BearerToken (JWT), TokenClaims, validation
- [ ] Wycheproof test vectors for Ed25519 and HMAC
- [ ] `keyring` integration for OS credential storage
- [ ] `zeroize` secure memory clearing

### Phase 2: QR & NFC (Week 3-4)
- [ ] Implement `veilpass_core::qr` — wrap `fast_qr`, add options/output types
- [ ] Implement `veilpass_core::nfc` — NDEF message building, URI/text/mime records
- [ ] QR decode verification tests (roundtrip)
- [ ] NFC encode/decode roundtrip tests
- [ ] CLI subcommands: `vp qr`, `vp nfc`

### Phase 3: Links & Signed URLs (Week 5-6)
- [ ] Implement `veilpass_core::links` — ClaimLink generation/verification
- [ ] Implement SignedUrl generation/verification
- [ ] Key derivation (HKDF-based sub-keys)
- [ ] Key export/import (encrypted bundles)
- [ ] CLI subcommands: `vp link`, `vp sign`, `vp key`, `vp verify`

### Phase 4: Desktop App (Week 7-8)
- [ ] Scaffold Tauri v2 app with React 19 + TypeScript + Vite
- [ ] Set up tauri-specta typed IPC
- [ ] Implement Tauri commands wrapping all core library functions
- [ ] Build UI: QR Generator, NFC Generator, Claim Link Form
- [ ] Build UI: Token Management, Key Management
- [ ] Build UI: Verification tool
- [ ] System tray + global shortcuts

### Phase 5: CI/CD & Distribution (Week 9-10)
- [ ] GitHub Actions CI: lint, test, security audit
- [ ] GitHub Actions release: multi-platform binaries
- [ ] Homebrew tap
- [ ] Docker image
- [ ] WASM build → npm package
- [ ] Auto-update for desktop app
- [ ] Documentation site (or README-driven)

### Phase 6: Hardening (Ongoing)
- [ ] Fuzz testing setup (`cargo fuzz`)
- [ ] Penetration testing (invite community review)
- [ ] Audit dependencies (`cargo audit` in CI)
- [ ] Performance benchmarking and optimization
- [ ] Internationalization (i18n) for desktop UI

---

## Appendix A: Key Design Decisions Summary

| Decision | Choice | Alternative Considered | Rationale |
|----------|--------|----------------------|-----------|
| Core language | Rust | Go, TypeScript | Memory safety for crypto, WASM target, Tauri requirement |
| Desktop shell | Tauri v2 | Electron, Wails | 30× smaller binary, native performance, OS keychain access |
| Frontend | React 19 + TS | Svelte, Vue | Mature ecosystem, TypeScript support, shadcn/ui |
| Signing algorithm | Ed25519 (primary), HS256 (secondary) | RSA, ECDSA | Compact signatures, fast, deterministic, side-channel resistant |
| JWT library | `jsonwebtoken` v11 | `oxitoken`, `jwt_compact` | Most mature, 2000+ stars, AWS-LC-RS backend |
| QR library | `fast_qr` v0.13 | `qrcode`, `image` | 7× faster, SVG + PNG + raw output |
| NDEF library | `ndef-rs` | `nanondef`, `ndef` | URI/text/mime support, active maintenance |
| Key storage | `keyring` v4 | Custom encrypted file | OS-native secure storage, cross-platform |
| IPC codegen | `tauri-specta` v2 | Manual invoke() | Compile-time type safety, eliminates drift |
| CLI parser | `clap` v4 (derive) | StructOpt, manual | De facto standard, derive API, env var support |

---

## Appendix B: Security Checklist (Pre-Release)

- [ ] All signing keys use `zeroize` on drop
- [ ] Algorithm is verified, not read from token header
- [ ] Clock skew leeway is bounded (default 30s, max 60s)
- [ ] Token TTL is bounded (default 24h, max 30d)
- [ ] No hardcoded keys or secrets in source code
- [ ] OS keychain used for persistent key storage
- [ ] No `unsafe` code in veilpass-core (except crypto FFI)
- [ ] All user input is length-bounded before processing
- [ ] QR code content is truncated/validated to prevent malicious data injection
- [ ] CLI does not echo secrets in process list (read from env var or stdin)
- [ ] `cargo audit` passes with zero known vulnerabilities
- [ ] `cargo deny` passes with approved license list
- [ ] Ed25519 public key validation (point-on-curve check)
- [ ] WASM target is securely isolated (no filesystem access from browser)

---

## Appendix C: Configuration File (`~/.veilpass/config.toml`)

```toml
[keys]
default_algorithm = "Ed25519"     # Ed25519 or HS256
auto_initialize = true            # Generate key on first run
keyring_service = "veilpass"      # OS keyring service name

[tokens]
default_ttl_seconds = 86400       # 24 hours
max_ttl_seconds = 2592000         # 30 days
clock_skew_leeway_seconds = 30
default_issuer = "veilpass"

[qr]
default_ecl = "H"                 # L, M, Q, H
default_width = 512
default_margin = 4

[nfc]
default_record_type = "URI"

[output]
default_format = "png"            # png, svg, terminal, raw
default_directory = "."           # Output directory
```

---

*This architecture document is a living blueprint. All major changes should be recorded in the project's decision log.*
