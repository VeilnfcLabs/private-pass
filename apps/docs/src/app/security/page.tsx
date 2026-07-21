export default function SecurityPage() {
  return (
    <div>
      <h1>Security</h1>

      <p>
        VeilPass is designed with security as a primary concern. This document outlines the
        security model, cryptographic primitives, threat model, and best practices for deploying
        VeilPass in production environments.
      </p>

      <h2>Security Model</h2>

      <p>
        VeilPass eliminates passwords entirely. Authentication is based on cryptographic
        challenges rather than shared secrets. The system uses a three-layer security model:
      </p>

      <ol>
        <li><strong>Transport Security</strong> &mdash; All API communication occurs over TLS 1.3. Certificates are enforced and mutual TLS (mTLS) is supported for server-to-server communication.</li>
        <li><strong>Credential Security</strong> &mdash; Tokens, links, and signatures use industry-standard cryptographic algorithms (HMAC-SHA256, RSA-2048, ECDSA P-256).</li>
        <li><strong>Usage Security</strong> &mdash; Time-to-live constraints, one-time use enforcement, and rate limiting prevent replay and brute force attacks.</li>
      </ol>

      <h2>Cryptographic Primitives</h2>

      <table>
        <thead>
          <tr>
            <th>Algorithm</th>
            <th>Use</th>
            <th>Key Size</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>HMAC-SHA256</td><td>Token signing, URL signing</td><td>256-bit</td></tr>
          <tr><td>HMAC-SHA384</td><td>Token signing (high security)</td><td>384-bit</td></tr>
          <tr><td>HMAC-SHA512</td><td>Token signing (maximum security)</td><td>512-bit</td></tr>
          <tr><td>RSA-2048</td><td>Key pair generation</td><td>2048-bit</td></tr>
          <tr><td>RSA-4096</td><td>Key pair generation (high security)</td><td>4096-bit</td></tr>
          <tr><td>ECDSA P-256</td><td>Key pair generation (modern)</td><td>256-bit</td></tr>
          <tr><td>SHA-256</td><td>Fingerprinting, hashing</td><td>256-bit</td></tr>
        </tbody>
      </table>

      <h2>Token Security</h2>

      <p>JWT tokens created by VeilPass include the following security features:</p>

      <ul>
        <li><strong>Expiration</strong> &mdash; Every token has an <code>exp</code> claim. Default TTL is 1 hour but can be configured down to minutes.</li>
        <li><strong>Unique ID</strong> &mdash; Each token includes a <code>jti</code> (JWT ID) claim, a UUID v4 that uniquely identifies the token.</li>
        <li><strong>Audience Restriction</strong> &mdash; Tokens are bound to a specific audience (<code>aud</code> claim) to prevent token reuse across services.</li>
        <li><strong>Issuer Verification</strong> &mdash; The <code>iss</code> claim identifies which service issued the token.</li>
        <li><strong>Revocation</strong> &mdash; Tokens can be revoked via the API. Revoked tokens are checked against a denylist.</li>
      </ul>

      <h2>Link Security</h2>

      <p>Claim links and signed URLs include:</p>

      <ul>
        <li><strong>Cryptographic Signatures</strong> &mdash; Each link includes an HMAC signature that authenticates the resource identifier and parameters.</li>
        <li><strong>Time Bounds</strong> &mdash; Links have explicit expiration timestamps encoded in the URL.</li>
        <li><strong>One-Time Use</strong> &mdash; Links can be configured to self-destruct after first use.</li>
        <li><strong>Usage Limits</strong> &mdash; Links can be restricted to a maximum number of uses.</li>
      </ul>

      <h2>Threat Model</h2>

      <p>VeilPass protects against the following threats:</p>

      <table>
        <thead>
          <tr>
            <th>Threat</th>
            <th>Mitigation</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>Phishing</td><td>No passwords to steal. Authentication is cryptographic and bound to the requesting context.</td></tr>
          <tr><td>Replay attacks</td><td>Short TTL, one-time use, and jti uniqueness prevent token reuse.</td></tr>
          <tr><td>Token leakage</td><td>Tokens are short-lived and bound to specific audiences and resources.</td></tr>
          <tr><td>Man-in-the-middle</td><td>TLS 1.3 for all API traffic. Signatures prevent parameter tampering.</td></tr>
          <tr><td>Brute force</td><td>Rate limiting on all API endpoints. Cryptographic algorithms have no practical brute force.</td></tr>
          <tr><td>SQL injection</td><td>Parameterized queries throughout. Input validation at every layer.</td></tr>
          <tr><td>Cross-site scripting</td><td>Content Security Policy headers. Output encoding. No HTML rendering of user data.</td></tr>
        </tbody>
      </table>

      <h2>Key Management</h2>

      <p>Best practices for managing cryptographic keys:</p>

      <ul>
        <li><strong>Key Rotation</strong> &mdash; Rotate signing keys regularly (every 90 days recommended).</li>
        <li><strong>Key Separation</strong> &mdash; Use separate keys for development, staging, and production environments.</li>
        <li><strong>Access Control</strong> &mdash; Private keys should only be accessible to the signing service.</li>
        <li><strong>Backup</strong> &mdash; Export and securely back up keys. Store backups in a hardware security module (HSM) or encrypted vault.</li>
        <li><strong>Audit</strong> &mdash; Log all key generation, export, and usage events.</li>
      </ul>

      <pre><code># Rotate keys regularly
veil key init                          # Generate new key
veil key export ./new-key.pub --public-only  # Export public key
# Update your services with the new public key
# Keep the old key until all tokens signed with it expire</code></pre>

      <h2>Production Deployment Checklist</h2>

      <ul>
        <li>Enable TLS 1.3 with a valid certificate from a trusted certificate authority.</li>
        <li>Set a strong, unique API key for your VeilPass server.</li>
        <li>Configure rate limiting appropriate for your expected traffic.</li>
        <li>Set reasonable default TTL values (1 hour or less).</li>
        <li>Enable audit logging for all authentication events.</li>
        <li>Use a dedicated secrets management service (e.g., HashiCorp Vault, AWS Secrets Manager) for storing signing keys.</li>
        <li>Configure CORS to allow only trusted origins.</li>
        <li>Regularly rotate API keys and signing keys.</li>
        <li>Monitor authentication logs for anomalous patterns.</li>
      </ul>

      <h2>Security Reporting</h2>

      <p>
        If you discover a security vulnerability in VeilPass, please report it privately to
        <code>security@veilpass.io</code>. We follow a responsible disclosure process and will
        acknowledge your report within 48 hours. Please do not disclose vulnerabilities publicly
        until we have had reasonable time to address them.
      </p>
    </div>
  );
}
