import Link from 'next/link';

export default function IntroductionPage() {
  return (
    <div>
      <h1>Introduction to VeilPass</h1>

      <p>
        VeilPass is an open-source, passwordless authentication and secure access management platform.
        It provides developers with a comprehensive toolkit for generating QR codes, NFC payloads,
        time-limited JSON Web Tokens (JWTs), and cryptographically signed links. VeilPass eliminates
        the need for traditional passwords by leveraging modern cryptographic standards.
      </p>

      <h2>What is VeilPass?</h2>

      <p>
        VeilPass is a multi-layered security platform that replaces password-based authentication with
        cryptographic challenges. Users authenticate by scanning QR codes, tapping NFC tags, or clicking
        signed links. The system uses short-lived tokens, one-time use constraints, and public-key
        cryptography to ensure that each authentication event is secure and verifiable.
      </p>

      <p>
        The platform consists of three main components:
      </p>

      <ul>
        <li><strong>CLI Tool</strong> (<code>veil</code>) &mdash; A command-line interface for generating credentials on demand.</li>
        <li><strong>REST API</strong> &mdash; A backend service for programmatic integration and server-side verification.</li>
        <li><strong>SDKs</strong> &mdash; Client libraries for embedding authentication in your applications.</li>
      </ul>

      <h2>Key Features</h2>

      <ul>
        <li><strong>QR Code Generation</strong> &mdash; Generate QR codes with configurable error correction, colors, and embedded metadata (expiry, one-time use).</li>
        <li><strong>NFC Payloads</strong> &mdash; Create NFC-compatible payloads in multiple formats (JSON, hex, base64, NDEF).</li>
        <li><strong>Signed Links</strong> &mdash; Generate cryptographically signed URLs with time-to-live and permission scoping.</li>
        <li><strong>JWT Tokens</strong> &mdash; Create and verify time-limited JWTs with custom claims.</li>
        <li><strong>Key Management</strong> &mdash; Generate, import, export, and manage cryptographic keys.</li>
        <li><strong>Verification</strong> &mdash; Verify tokens, links, URLs, and signatures from a single command.</li>
      </ul>

      <h2>Use Cases</h2>

      <ul>
        <li><strong>Zero-signup authentication</strong> &mdash; Users scan a QR code or tap an NFC tag to authenticate instantly.</li>
        <li><strong>Secure document sharing</strong> &mdash; Generate one-time access links for sensitive documents.</li>
        <li><strong>Physical access control</strong> &mdash; NFC tags on doors or devices grant time-limited access.</li>
        <li><strong>API authentication</strong> &mdash; Issue short-lived JWTs for service-to-service communication.</li>
        <li><strong>Event ticketing</strong> &mdash; Generate scannable QR codes that expire after the event.</li>
      </ul>

      <h2>How It Works</h2>

      <p>
        VeilPass uses a challenge-response model. The server or CLI generates a signed token, QR code,
        or NFC payload that contains cryptographic proof of authenticity. When the client presents this
        credential, the verifying party checks the signature, expiry, and any usage constraints. Since
        passwords are never exchanged, there is no risk of credential leakage through phishing or database
        breaches.
      </p>

      <h2>Next Steps</h2>

      <ul>
        <li><Link href="/installation">Install VeilPass</Link> &mdash; Set up the CLI tool on your platform.</li>
        <li><Link href="/quickstart">Quick Start Guide</Link> &mdash; Generate your first QR code and token in minutes.</li>
        <li><Link href="/cli">CLI Reference</Link> &mdash; Explore all available commands and options.</li>
      </ul>
    </div>
  );
}
