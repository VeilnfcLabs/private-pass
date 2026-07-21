# Contributing to VeilPass

Thank you for considering contributing to VeilPass! This document outlines the
development process, coding standards, and guidelines for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Pull Request Process](#pull-request-process)
7. [Security Considerations](#security-considerations)

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
By participating, you agree to uphold its standards.

## Development Setup

### Prerequisites

- **Rust** 1.85+ (`rustup install stable`)
- **Node.js** 22+ (with pnpm)
- **Python** 3.12+
- **Docker** (optional, for running the API locally)

### Clone and Build

```bash
# Clone the repository
git clone https://github.com/veillabs/private-pass.git
cd private-pass

# Install Rust toolchain
rustup toolchain install stable
rustup target add wasm32-unknown-unknown

# Install Node.js dependencies
pnpm install

# Install Python dependencies
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ../..

# Build the Rust CLI
cargo build -p veilpass-cli

# Build the npm CLI
cd cli
npm install
npm run build
cd ..

# Build the web frontend
cd apps/web
npm install
npm run build
cd ../..
```

### Development Servers

```bash
# API server (hot-reload)
cd apps/api
uvicorn app.main:app --reload --port 8000

# Web frontend (hot-reload)
cd apps/web
npm run dev

# CLI (live TypeScript)
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
├── cli/               # npm CLI tool
├── crates/
│   ├── veilpass-cli/  # Rust CLI binary
│   ├── veilpass-core/ # Core Rust library (crypto, QR, NFC, tokens)
│   └── veilpass-tauri/ # Tauri desktop app backend
├── docker/            # Docker Compose configuration
├── packages/          # Shared packages
├── scripts/           # Setup and utility scripts
└── src/               # Tauri frontend (React + TypeScript)
```

## Coding Standards

### Rust

- **Format:** All Rust code must pass `cargo fmt`
- **Lint:** All Rust code must pass `cargo clippy --all-targets -- -D warnings`
- **No unsafe code** in `veilpass-core` (except crypto FFI with justification)
- **Error handling:** Use `thiserror` for library errors, `anyhow` for application errors
- **Documentation:** All public API items must have doc comments (`///`)
- **Naming:** Follow Rust naming conventions (snake_case, CamelCase)

### Python

- **Format:** Follow PEP 8 with 100-character line limit
- **Lint:** All Python code must pass `ruff check` and `pylint` (score ≥ 8.0)
- **Type hints:** All functions must have type annotations
- **Documentation:** Use docstrings for all public modules, classes, and functions

### TypeScript / JavaScript

- **Format:** All TS/JS code must pass `biome check`
- **Lint:** All TS/JS code must pass `biome lint`
- **TypeScript:** Enable `strict` mode; avoid `any` wherever possible
- **Naming:** Use camelCase for variables/functions, PascalCase for components
- **React:** Use functional components with hooks; avoid class components

### General

- **No secrets** in code: keys, tokens, passwords must come from environment variables
- **No large files:** Keep files under 500 lines; refactor into modules if needed
- **Comments:** Write self-documenting code first; add comments for complex logic
- **Commit messages:** Use conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, etc.)

## Testing Requirements

### Before submitting a PR, ensure:

1. **Rust tests pass:** `cargo test --workspace --all-features`
2. **Python tests pass:** `cd apps/api && python -m pytest tests/`
3. **TypeScript type checks:** `pnpm typecheck`
4. **CLI builds:** `cd cli && npm run build`
5. **Lint checks pass:** `cargo clippy`, `ruff check`, `biome check`
6. **Security audit:** `cargo audit`, `npm audit`

### Test Coverage Requirements

- **Core library:** ≥ 90% coverage for crypto/signing modules
- **API endpoints:** Integration tests for all routes
- **CLI commands:** End-to-end tests for all subcommands
- **Frontend:** Unit tests for state management and utilities

### Writing Tests

- Use `#[cfg(test)]` modules for unit tests in Rust
- Use `tests/` directory for integration tests in Rust
- Use `pytest` for Python tests
- Use `vitest` for TypeScript tests

## Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes** following the coding standards above.

3. **Write or update tests** to cover your changes.

4. **Run all checks locally:**
   ```bash
   cargo test --workspace --all-features
   cargo clippy --workspace --all-targets -- -D warnings
   cargo fmt --all --check
   cd apps/api && python -m pytest tests/ && cd ../..
   cd cli && npm run build && cd ..
   biome check .
   ```

5. **Commit your changes** using conventional commits:
   ```bash
   git commit -m "feat(qr): add support for Micro QR codes"
   ```

6. **Push and create a PR:**
   ```bash
   git push origin feat/my-feature
   # Then open a PR on GitHub
   ```

7. **PR review requirements:**
   - At least one approval from a code owner
   - All CI checks pass (lint, test, build, security)
   - No merge conflicts with `main`

8. **Merge:** Squash and merge for feature branches; rebase for release branches.

## Security Considerations

- Never hardcode keys, tokens, or credentials
- Use environment variables for all secrets
- Avoid printing or logging sensitive data (keys, tokens)
- Follow the principle of least privilege
- Report security vulnerabilities via `security@veillabs.dev`
- See [SECURITY.md](SECURITY.md) for the full security policy

## Questions?

If you have questions about contributing, open a [Discussion](https://github.com/veillabs/private-pass/discussions)
or ask in the Veil Labs community channels.
