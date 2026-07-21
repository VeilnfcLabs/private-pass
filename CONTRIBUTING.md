# Contributing to VeilPass

Thank you for your interest in contributing to VeilPass! We're building
privacy-first cryptographic tools and welcome contributions of all kinds.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Security Considerations](#security-considerations)

## Code of Conduct

This project adheres to the [Contributor Covenant](.github/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Report unacceptable
behavior to `conduct@veillabs.dev`.

## Development Setup

### Prerequisites

- **Rust** 1.85+ (`rustup install stable`)
- **Node.js** 22+ (with pnpm or npm)
- **Python** 3.12+
- **Docker** (optional, for API and database services)

### Clone and Initialize

```bash
# Clone the repository
git clone https://github.com/veillabs/private-pass.git
cd private-pass

# Run the platform-appropriate setup script
# macOS/Linux:
chmod +x scripts/setup.sh && ./scripts/setup.sh

# Windows PowerShell:
.\scripts\setup.ps1
```

### Manual Setup

```bash
# 1. Rust toolchain
rustup toolchain install stable
rustup target add wasm32-unknown-unknown

# 2. Build the Rust CLI
cargo build -p veilpass-cli

# 3. Run Rust tests
cargo test --workspace --all-features

# 4. npm CLI
cd cli
npm install
npm run build
cd ..

# 5. Python API
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ../..
```

### Development Servers

```bash
# API (hot-reload)
cd apps/api
uvicorn app.main:app --reload --port 8000

# Web frontend (Next.js)
cd apps/web
npm run dev

# CLI (TypeScript watch mode)
cd cli
npm run dev -- qr "https://example.com"
```

## Project Structure

```
veilpass/
├── apps/
│   ├── api/           # FastAPI Python backend
│   ├── docs/          # Documentation site
│   └── web/           # Next.js frontend
├── cli/               # npm CLI tool (TypeScript)
├── crates/
│   ├── veilpass-cli/  # Rust CLI binary (vp)
│   ├── veilpass-core/ # Core Rust library
│   └── veilpass-tauri/ # Tauri desktop app
├── docker/            # Docker Compose configuration
├── packages/          # Shared packages
├── scripts/           # Setup and utility scripts
└── src/               # Tauri frontend (React + Vite)
```

## Coding Standards

### Rust

- **Format:** All code must pass `cargo fmt`
- **Lint:** All code must pass `cargo clippy --all-targets -- -D warnings`
- **No unsafe code** in core library (justify any exceptions in crypto FFI)
- **Error handling:** Use `thiserror` for library errors, `anyhow` for binaries
- **Documentation:** Document all public API items with `///` doc comments

### Python

- **Format:** PEP 8 with 100-character line limit
- **Lint:** Must pass `ruff check` and `pylint` (score ≥ 8.0)
- **Type hints:** Required for all function signatures

### TypeScript / JavaScript

- **Format:** Must pass `biome check`
- **Strict TypeScript:** Enable `strict` mode; minimize `any` usage
- **React:** Use functional components with hooks

## Testing Requirements

Before submitting a pull request, ensure:

```bash
# Rust: all tests pass
cargo test --workspace --all-features

# Rust: clippy clean
cargo clippy --workspace --all-targets -- -D warnings

# Rust: formatting correct
cargo fmt --all --check

# Python: tests pass
cd apps/api && python -m pytest tests/ -v && cd ../..

# Python: lint clean
ruff check apps/api/
pylint apps/api/ --exit-zero --max-line-length=100

# TypeScript: type checks pass
cd cli && npx tsc --noEmit && cd ..

# JavaScript/TypeScript: biome clean
biome check .

# Security audit
cargo audit
```

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/your-feature
   ```

2. **Make your changes** following the coding standards.

3. **Add tests** for new functionality.

4. **Run all checks** (see testing requirements above).

5. **Commit with a conventional commit message:**
   ```
   feat(qr): add support for animated QR codes
   fix(nfc): correct NDEF record length encoding
   docs: update API examples
   ```

6. **Push and create a PR** — fill out the PR template completely.

7. **Address review feedback** — maintainers will review and may request changes.

8. **Merge** — once approved and CI passes, a maintainer will merge.

## Security Considerations

- **No secrets in code** — use environment variables for all keys and tokens
- **Zero unsafe code** in core — cryptographic safety is paramount
- **Input validation** — validate and sanitize all user inputs
- **Report vulnerabilities** privately to `security@veillabs.dev`
- See [SECURITY.md](SECURITY.md) for the full security policy

## Questions?

- Open a [Discussion](https://github.com/veillabs/private-pass/discussions)
- Email: `hello@veillabs.dev`
- Docs: `https://veilpass.app/docs`
