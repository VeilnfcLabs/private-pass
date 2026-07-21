# Security Policy

## Supported Versions

The latest stable release of VeilPass receives security updates.
Older versions may receive critical patches on a case-by-case basis.

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

**Do not** open a public GitHub issue for security vulnerabilities.
Report privately to: **security@veillabs.dev**

### What to Include

- Description of the vulnerability
- Steps to reproduce (proof of concept preferred)
- Affected versions and components
- Potential impact
- Suggested fix (if known)

### PGP Key

```
Fingerprint: A1B2 C3D4 E5F6 7890 1234 5678 9ABC DEF0 1234 5678
Download: https://veillabs.dev/security/pgp-key.asc
```

### Response Timeline

| Timeframe | Action |
|-----------|--------|
| 24 hours  | Acknowledgment of receipt |
| 72 hours  | Triage and severity assessment |
| 7 days    | Fix in development (critical/high) |
| 14 days   | Fix in development (medium) |
| 30 days   | Fix in development (low) |
| Upon release | Public disclosure + CVE |

## Security Features

- **Ed25519 signatures** — Deterministic, constant-time, side-channel resistant
- **OS keychain storage** — Keys stored via `keyring` crate (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Secure memory** — `zeroize` on drop for all cryptographic material
- **Algorithm lockdown** — Verifier specifies algorithm, preventing confusion attacks
- **Bounded TTL** — Tokens have configurable but bounded expiration (max 30 days)
- **Replay prevention** — Unique `jti` (UUID v7) for each token
- **Dependency auditing** — Automated `cargo audit`, `npm audit`, and `safety` in CI

## Security Advisories

Published at: https://github.com/veillabs/private-pass/security/advisories

## Bug Bounty

We do not currently offer a formal bug bounty program, but we publicly credit
all valid security researchers who responsibly disclose vulnerabilities.
