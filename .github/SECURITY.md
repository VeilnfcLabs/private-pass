# Security Policy

## Supported Versions

We currently support the latest stable release of VeilPass with security updates.
Older versions may receive critical security patches on a case-by-case basis.

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

VeilPass takes security seriously. If you discover a security vulnerability,
please **do not** open a public GitHub issue. Instead, report it privately.

### How to Report

1. **Email:** `security@veillabs.dev` — Encrypted emails preferred using our PGP key.
2. **PGP Key:** Available at `https://veillabs.dev/security/pgp-key.asc`
   - Fingerprint: `A1B2 C3D4 E5F6 7890 1234 5678 9ABC DEF0 1234 5678`
3. **GitHub Security Advisory:** Use the "Report a vulnerability" button on the
   [Security Advisories](https://github.com/veillabs/private-pass/security/advisories) page.

### What to Include

- Description of the vulnerability
- Steps to reproduce (PoC preferred)
- Affected versions and components
- Potential impact
- Any suggested fix (if known)

### Response Timeline

| Timeframe        | Action                          |
|-----------------|---------------------------------|
| 24 hours        | Acknowledgment of receipt       |
| 72 hours        | Initial triage and severity assessment |
| 7 days          | Fix in development (critical)   |
| 14 days         | Fix in development (high)       |
| 30 days         | Fix in development (medium/low) |
| Upon release    | Public disclosure + CVE assignment |

After a fix is released, we will publicly acknowledge your responsible disclosure
unless you prefer to remain anonymous.

## Security Features

- **Ed25519 digital signatures** — Deterministic, constant-time verification
- **Key isolation** — OS keychain storage via `keyring` crate
- **Secure memory** — `zeroize` on drop for all cryptographic keys
- **Algorithm lockdown** — Verifier specifies algorithm, not the token
- **JWT best practices** — Bounded TTL, `jti` for replay prevention, clock skew limits
- **No unsafe code** — Core library has zero `unsafe` blocks (except crypto FFI)
- **Dependency auditing** — `cargo audit`, `npm audit`, `safety` run in CI

## Bug Bounty

We currently do not offer a formal bug bounty program, but we deeply appreciate
and publicly credit all valid security researchers who responsibly disclose issues.

## Disclosure Policy

We follow a coordinated disclosure process:
1. Reporter submits vulnerability (private)
2. We validate and triage
3. We develop and test a fix
4. We release a patched version
5. We publish a security advisory (with CVE if applicable)
6. We credit the reporter (with permission)

## Security Advisories

All security advisories are published at:
https://github.com/veillabs/private-pass/security/advisories
