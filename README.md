# VeilPass

> **Privacy-first QR code, NFC tag, and cryptographic token generator**

<p align="center">
  <a href="https://github.com/veillabs/private-pass/actions"><img src="https://img.shields.io/github/actions/workflow/status/veillabs/private-pass/ci.yml?branch=main&style=flat-square&logo=github" alt="CI Status"></a>
  <a href="https://crates.io/crates/veilpass-core"><img src="https://img.shields.io/crates/v/veilpass-core?style=flat-square&logo=rust" alt="Crates.io"></a>
  <a href="https://www.npmjs.com/package/veilpass-cli"><img src="https://img.shields.io/npm/v/veilpass-cli?style=flat-square&logo=npm" alt="npm"></a>
  <a href="https://github.com/veillabs/private-pass/blob/main/LICENSE"><img src="https://img.shields.io/github/license/veillabs/private-pass?style=flat-square" alt="License"></a>
  <a href="https://docs.rs/veilpass-core"><img src="https://img.shields.io/docsrs/veilpass-core?style=flat-square&logo=docsdotrs" alt="Docs"></a>
  <a href="https://github.com/veillabs/private-pass/releases"><img src="https://img.shields.io/github/v/release/veillabs/private-pass?style=flat-square&logo=github" alt="Release"></a>
</p>

---

## Overview

VeilPass is a comprehensive privacy-focused tool for generating cryptographically
signed QR codes, NFC tags, secure claim links, and time-limited tokens. Built with
a **Rust core** for maximum security and performance, it provides:

- **Desktop app** (Tauri v2) with a modern React UI
- **CLI** (`vp` / `veilpass`) for headless and CI environments
- **FastAPI backend** for web and API access
- **npm package** for Node.js integration
- **WASM module** for browser embedding

All cryptographic operations use **Ed25519** (primary) or **HMAC-SHA256** for
digital signatures, with keys stored securely in the OS keychain.

---

## Key Features

- **QR Code Generation** — Generate QR codes in PNG, SVG, or raw matrix format with configurable error correction (ECL L/M/Q/H)
- **NFC Tag Encoding** — Create NDEF records (URI, Text, Smart Poster) ready for writing to NFC tags
- **Secure Claim Links** — Generate Ed25519-signed claim links for secure resource sharing with optional one-time use
- **Signed URLs** — Create time-limited signed URLs with cryptographic verification
- **Bearer Tokens** — Issue and verify JWT tokens with configurable TTL, scope, and audience
- **Key Management** — Generate, export, import, and manage Ed25519 and HMAC-SHA256 keys via OS keychain
- **Verification** — Verify tokens, claim links, and signatures to ensure authenticity
- **Cross-Platform** — Desktop app (Windows, macOS, Linux), CLI (all platforms), and web interface

---

## Quick Start

### CLI

```bash
# Install via npm
npm install -g veilpass-cli

# Generate a QR code
veilpass qr "https://example.com" --output qr.png

# Generate a secure claim link
veilpass link create "resource://tickets/vip-001" --ttl 24h --one-time

# Issue a bearer token
veilpass token issue --sub user-001 --ttl 7d --scope "read:tickets"

# Verify a token
veilpass verify token "eyJhbGciOiJFZERTQSJ9..."
```

### Rust Library

```toml
[dependencies]
veilpass-core = "0.1"
```

```rust
use veilpass_core::qr::{self, QrOptions};
use veilpass_core::signing::SigningKey;
use veilpass_core::links::ClaimLink;

// Generate a QR code
let png = qr::generate_png("https://example.com")?;

// Generate a secure claim link
let key = SigningKey::generate();
let link = ClaimLink::generate(
    "resource://tickets/vip-001",
    &key,
    &TokenConfig::default(),
    true,
)?;
println!("{}", link.url);
```

### API

```bash
# Start the API server
cd apps/api
uvicorn app.main:app --port 8000

# Generate a QR code
curl -X POST http://localhost:8000/qr/generate \
  -H "Content-Type: application/json" \
  -d '{"content": "https://example.com", "format": "png"}'

# Verify a token
curl -X POST http://localhost:8000/verify/token \
  -H "Content-Type: application/json" \
  -d '{"token": "eyJhbGciOiJFZERTQSJ9..."}'
```

### Docker

```bash
# Start the full stack
docker compose -f docker/docker-compose.yml up -d

# Access the web UI at http://localhost:3000
# Access the API at http://localhost:8000/docs
```

---

## Documentation

- [Architecture Document](ARCHITECTURE.md) — Full system architecture and design decisions
- [Rust API Docs](https://docs.rs/veilpass-core) — Core library documentation
- [CLI Reference](https://github.com/veillabs/private-pass#cli-usage) — CLI command reference
- [API Reference](https://github.com/veillabs/private-pass#api-usage) — REST API documentation
- [Docker Setup](docker/README.md) — Docker Compose instructions

---

## CLI Examples

```bash
# QR codes
vp qr "https://example.com"                    # PNG output
vp qr "https://example.com" -f svg -o output   # SVG output
vp qr "https://example.com" --ecl H --width 1024

# NFC payloads
vp nfc uri "https://example.com" -o tag.bin
vp nfc text "Hello, World!" -l fr
vp nfc smart-poster "Check this out" "https://example.com"

# Claim links
vp link create "resource://docs/secret.pdf" --ttl 7d
vp link create "resource://ticket/vip" --ttl 1h --one-time

# Signed URLs
vp sign url "https://api.example.com/files/doc.pdf" --ttl 1h

# Tokens
vp token issue --sub user-001 --ttl 24h --scope "read write"
vp token issue --sub service-01 --ttl 30d --audience "api.example.com"

# Key management
vp key init
vp key list
vp key export backup.key --passphrase "strong-passphrase"
vp key import backup.key --passphrase "strong-passphrase"

# Verification
vp verify token "eyJhbGciOiJFZERTQSJ9..."
vp verify link "https://claim.veilpass.app/c/eyJhbGciOiJFZERTQSJ9..."
```

---

## API Examples

### Generate QR Code

```bash
curl -X POST http://localhost:8000/qr/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "https://example.com",
    "format": "png",
    "ecl": "H",
    "width": 512
  }' \
  --output qr.png
```

### Create Claim Link

```bash
curl -X POST http://localhost:8000/links/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "resource": "resource://tickets/vip-001",
    "ttl_seconds": 86400,
    "one_time": true
  }'
```

### Issue Bearer Token

```bash
curl -X POST http://localhost:8000/tokens/issue \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{
    "subject": "user-001",
    "ttl_seconds": 604800,
    "scope": ["read:tickets", "write:tickets"]
  }'
```

### Verify Token

```bash
curl -X POST http://localhost:8000/verify/token \
  -H "Content-Type: application/json" \
  -d '{"token": "eyJhbGciOiJFZERTQSJ9..."}'
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Core** | Rust (edition 2021) | Cryptographic operations, QR/NFC generation |
| **CLI** | Rust (clap) + TypeScript (npm) | Command-line interface |
| **Desktop** | Tauri v2 + React 19 | Native desktop application |
| **Frontend** | Next.js 15 + React 19 + Tailwind CSS v4 | Web interface |
| **Backend** | FastAPI (Python 3.12) | REST API |
| **Database** | PostgreSQL 16 | Persistent storage |
| **Cache** | Redis 7 | Rate limiting, session cache |
| **Documentation** | Markdown + docs.rs | Technical documentation |
| **CI/CD** | GitHub Actions | Automated testing and releases |
| **Container** | Docker + Docker Compose | Local development and deployment |

---

## Project Structure

```
veilpass/
├── .github/                    # GitHub Actions, templates, policies
│   ├── workflows/
│   │   ├── ci.yml              # Continuous integration
│   │   └── release.yml         # Build and publish releases
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── CODEOWNERS              # Code ownership
├── apps/
│   ├── api/                    # FastAPI backend
│   ├── docs/                   # Documentation site
│   └── web/                    # Next.js frontend
├── cli/                        # npm CLI tool (TypeScript)
├── crates/
│   ├── veilpass-core/          # Core Rust library
│   ├── veilpass-cli/           # Rust CLI binary (vp)
│   └── veilpass-tauri/         # Tauri desktop backend
├── docker/                     # Docker Compose configuration
├── packages/                   # Shared packages
├── scripts/                    # Setup and utility scripts
├── src/                        # Tauri frontend (React + Vite)
├── Cargo.toml                  # Rust workspace
├── package.json                # Root package.json
└── ARCHITECTURE.md             # Architecture documentation
```

---

## Docker Usage

```bash
# Full stack (API + Web + Docs + DB + Redis)
docker compose -f docker/docker-compose.yml up -d

# Individual services
docker compose -f docker/docker-compose.yml up api
docker compose -f docker/docker-compose.yml up web

# Build and push images
docker build -f docker/Dockerfile.api -t veilpass-api .
docker build -f docker/Dockerfile.web -t veilpass-web .

# See docker/README.md for full documentation
```

---

## Contributing

We welcome contributions! Please see:

- [Contributing Guide](CONTRIBUTING.md) — Development setup, coding standards, PR process
- [Code of Conduct](.github/CODE_OF_CONDUCT.md) — Community standards
- [Security Policy](SECURITY.md) — Vulnerability reporting

---

## License

VeilPass is released under the [MIT License](LICENSE).

---

<p align="center">
  <sub>Built with ❤️ by </sub>
  <a href="https://veillabs.dev"><strong>Veil Labs</strong></a>
  <sub> — Privacy-first security tools</sub>
</p>
