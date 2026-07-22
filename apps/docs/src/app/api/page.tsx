export default function ApiPage() {
  return (
    <div>
      <h1>REST API Reference</h1>

      <p>
        The VeilPass REST API provides programmatic access to all platform features.
        The API is organized around REST principles and uses JSON for request and response bodies.
        All endpoints are prefixed with <code>/api</code>.
      </p>

      <h2>Base URL</h2>

      <pre><code>https://api.veilpass.io/api</code></pre>

      <p>For local development:</p>

      <pre><code>http://localhost:8000/api</code></pre>

      <h2>Authentication</h2>

      <p>
        API requests require an API key sent in the <code>X-API-Key</code> header.
        Obtain an API key from the VeilPass dashboard or by contacting your administrator.
      </p>

      <pre><code>X-API-Key: vp_api_abc123def456</code></pre>

      <h2>Health Check</h2>

      <p>Check the API server status.</p>

      <pre><code>GET /api/health</code></pre>

      <p>Response:</p>

      <pre><code>{
  "status": "ok",
  "version": "0.1.0",
  "uptime": 3600
}</code></pre>

      <h2>QR Codes</h2>

      <h3>Create QR Code</h3>

      <pre><code>POST /api/qr</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "content": "https://veilpass.io/claim/abc123",
  "options": {
    "format": "png",
    "error_correction_level": "M",
    "width": 256,
    "margin": 4,
    "foreground_color": "#000000",
    "background_color": "#ffffff",
    "expires_in": 3600,
    "one_time": true
  }
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "id": "qr_a1b2c3d4",
  "qr_code": "data:image/png;base64,iVBOR...",
  "format": "png",
  "created_at": "2026-07-22T02:00:00Z",
  "expires_at": "2026-07-22T03:00:00Z",
  "one_time": true
}</code></pre>

      <h3>Get QR Code</h3>

      <pre><code>GET /api/qr/:id</code></pre>

      <p>Response:</p>

      <pre><code>{
  "id": "qr_a1b2c3d4",
  "content": "https://veilpass.io/claim/abc123",
  "format": "png",
  "created_at": "2026-07-22T02:00:00Z",
  "expires_at": "2026-07-22T03:00:00Z",
  "one_time": true,
  "used": false
}</code></pre>

      <h2>Tokens</h2>

      <h3>Create Token</h3>

      <pre><code>POST /api/tokens</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "sub": "user_42",
  "aud": "my-api",
  "iss": "veilpass",
  "ttl": 3600,
  "claims": {
    "role": "admin",
    "department": "engineering"
  }
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-07-22T03:00:00Z",
  "issued_at": "2026-07-22T02:00:00Z",
  "id": "tok_x1y2z3w4"
}</code></pre>

      <h3>Verify Token</h3>

      <pre><code>POST /api/tokens/verify</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "valid": true,
  "payload": {
    "sub": "user_42",
    "aud": "my-api",
    "iss": "veilpass",
    "iat": 1700000000,
    "exp": 1700003600,
    "jti": "uuid-here",
    "role": "admin",
    "department": "engineering"
  }
}</code></pre>

      <h3>Revoke Token</h3>

      <pre><code>DELETE /api/tokens/:id</code></pre>

      <p>Response:</p>

      <pre><code>{
  "revoked": true,
  "id": "tok_x1y2z3w4"
}</code></pre>

      <h2>Claim Links</h2>

      <h3>Create Claim Link</h3>

      <pre><code>POST /api/links</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "resource": "resource:doc-42",
  "ttl": 3600,
  "one_time": true,
  "max_uses": 1,
  "permissions": ["read", "download"]
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "id": "lnk_a1b2c3d4",
  "url": "https://veilpass.io/claim?r=resource:doc-42&exp=1700003600&ot=true&mu=1&s=sig_abc",
  "expires_at": "2026-07-22T03:00:00Z",
  "one_time": true,
  "max_uses": 1,
  "resource": "resource:doc-42"
}</code></pre>

      <h3>Verify Claim Link</h3>

      <pre><code>POST /api/links/verify</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "url": "https://veilpass.io/claim?r=resource:doc-42&exp=1700003600&s=sig_abc"
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "valid": true,
  "resource": "resource:doc-42",
  "expired": false,
  "one_time": true,
  "remaining_uses": 0,
  "signature_valid": true
}</code></pre>

      <h2>NFC Payloads</h2>

      <h3>Generate NFC Payload</h3>

      <pre><code>POST /api/nfc</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "type": "uri",
  "payload": "https://veilpass.io/claim/door-42",
  "issuer": "Building-A",
  "version": "1.0",
  "format": "ndef"
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "id": "nfc_x1y2z3w4",
  "payload": "0155020b...",
  "format": "ndef",
  "type": "uri",
  "issuer": "Building-A",
  "created_at": "2026-07-22T02:00:00Z"
}</code></pre>

      <h2>Signatures</h2>

      <h3>Sign Message</h3>

      <pre><code>POST /api/sign</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "data": "message-to-sign",
  "key_id": "vk-abc123",
  "permissions": ["read"]
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "signature": "abc123def456...",
  "key_id": "vk-abc123",
  "algorithm": "HS256",
  "signed_at": "2026-07-22T02:00:00Z"
}</code></pre>

      <h3>Verify Signature</h3>

      <pre><code>POST /api/sign/verify</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "data": "message-to-sign",
  "signature": "abc123def456...",
  "key_id": "vk-abc123"
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "valid": true,
  "key_id": "vk-abc123",
  "algorithm": "HS256",
  "verified_at": "2026-07-22T02:05:00Z"
}</code></pre>

      <h2>Keys</h2>

      <h3>List Keys</h3>

      <pre><code>GET /api/keys</code></pre>

      <p>Response:</p>

      <pre><code>{
  "keys": [
    {
      "id": "vk-abc123",
      "algorithm": "RSA-2048",
      "fingerprint": "a1b2c3d4e5f6g7h8",
      "created_at": "2026-07-22T02:00:00Z",
      "public_key": "-----BEGIN PUBLIC KEY-----\n..."
    }
  ]
}</code></pre>

      <h3>Create Key</h3>

      <pre><code>POST /api/keys</code></pre>

      <p>Response:</p>

      <pre><code>{
  "id": "vk-def456",
  "algorithm": "RSA-2048",
  "fingerprint": "i9j0k1l2m3n4o5p6",
  "created_at": "2026-07-22T02:00:00Z",
  "public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n..."
}</code></pre>

      <div className="callout callout-warning">
        The private key is only returned once at creation time. Store it securely.
      </div>

      <h2>SD-JWT — Selective Disclosure JWTs</h2>

      <h3>Create SD-JWT</h3>

      <pre><code>POST /api/v1/token/sd-jwt</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "claims": {
    "sub": "user_42",
    "email": "user@example.com",
    "role": "admin"
  },
  "issuer": "VeilPass"
}</code></pre>

      <p>Response:</p>

      <pre><code>{
  "sd_jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6InNkK2p3dCJ9...",
  "disclosures": ["salt1:email_value", "salt2:role_value"]
}</code></pre>

      <h3>Present SD-JWT</h3>

      <pre><code>POST /api/v1/token/sd-jwt/present</code></pre>

      <p>Response includes only the selected claim disclosures.</p>

      <h3>Verify SD-JWT</h3>

      <pre><code>POST /api/v1/verify/sd-jwt</code></pre>

      <h2>ZKP — Zero-Knowledge Proofs</h2>

      <h3>Generate Keypair</h3>

      <pre><code>POST /api/v1/zkp/keypair</code></pre>

      <p>Request body:</p>

      <pre><code>{
  "secret": "user-secret"
}</code></pre>

      <p>Response: <code>{ "public_key": "...", "commitment": "..." }</code></p>

      <h3>Generate Proof</h3>

      <pre><code>POST /api/v1/zkp/proof</code></pre>

      <p>Response: <code>{ "challenge": "...", "response": "...", "nonce": "..." }</code></p>

      <h3>Verify Proof</h3>

      <pre><code>POST /api/v1/zkp/verify</code></pre>

      <p>Response: <code>{ "valid": true/false }</code></p>

      <h2>Ephemeral Credentials</h2>

      <h3>Create Ephemeral Credential</h3>

      <pre><code>POST /api/v1/ephemeral</code></pre>

      <p>Request:</p>

      <pre><code>{
  "content": "sensitive-data",
  "ttl": 600,
  "one_time": true
}</code></pre>

      <p>Response: <code>{ "token": "ep_ot_...", "expires_at": "..." }</code></p>

      <h3>Verify Ephemeral Credential</h3>

      <pre><code>POST /api/v1/ephemeral/verify</code></pre>

      <h2>Encrypted Payloads</h2>

      <h3>Encrypt</h3>

      <pre><code>POST /api/v1/encrypted</code></pre>

      <p>Request:</p>

      <pre><code>{
  "content": "sensitive-data",
  "password": "user-password"
}</code></pre>

      <p>Response includes ciphertext, nonce, tag, QR payload, and NFC payload.</p>

      <h3>Decrypt</h3>

      <pre><code>POST /api/v1/encrypted/decrypt</code></pre>

      <h2>Trust Registry</h2>

      <h3>Register Issuer</h3>

      <pre><code>POST /api/v1/registry</code></pre>

      <p>Request:</p>

      <pre><code>{
  "did": "did:veilpass:abc123",
  "name": "My Org",
  "public_key": "-----BEGIN PUBLIC KEY-----..."
}</code></pre>

      <h3>List Issuers</h3>

      <pre><code>GET /api/v1/registry</code></pre>

      <h3>Lookup Issuer</h3>

      <pre><code>GET /api/v1/registry/{did}</code></pre>

      <h3>Verify Issuer</h3>

      <pre><code>POST /api/v1/registry/verify</code></pre>

      <h2>QR Analytics</h2>

      <h3>Get Analytics</h3>

      <pre><code>GET /api/v1/dynamic-qr/{id}/analytics</code></pre>

      <p>Returns scans over time, top agents, top referrers, unique IPs, and privacy mode.</p>

      <h3>Privacy Score</h3>

      <pre><code>GET /api/v1/dynamic-qr/{id}/privacy-score</code></pre>

      <p>Returns a privacy compliance score with GDPR and Kenya DPA compliance indicators.</p>

      <h2>Webhooks</h2>

      <h3>Register Webhook</h3>

      <pre><code>POST /api/v1/webhooks</code></pre>

      <p>Request:</p>

      <pre><code>{
  "url": "https://example.com/webhook",
  "events": ["token.issued", "token.verified", "qr.scanned"],
  "secret": "webhook-signing-secret"
}</code></pre>

      <h3>List Webhooks</h3>

      <pre><code>GET /api/v1/webhooks</code></pre>

      <h3>Delete Webhook</h3>

      <pre><code>DELETE /api/v1/webhooks/{id}</code></pre>

      <h2>Key Rotation</h2>

      <h3>Rotate Keys</h3>

      <pre><code>POST /api/v1/keys/rotate</code></pre>

      <p>Creates a new active key and retains the old key for verification of previously signed credentials.</p>

      <h3>List Keys</h3>

      <pre><code>GET /api/v1/keys</code></pre>

      <h2>Audit Logging</h2>

      <h3>Get Audit Log</h3>

      <pre><code>GET /api/v1/audit</code></pre>

      <h3>Export Audit Log</h3>

      <pre><code>GET /api/v1/audit/export</code></pre>

      <p>Returns audit log as CSV for external analysis.</p>

      <h2>Error Handling</h2>

      <p>The API uses conventional HTTP status codes:</p>

      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>200</td><td>Success</td></tr>
          <tr><td>201</td><td>Created</td></tr>
          <tr><td>400</td><td>Bad Request &mdash; invalid input</td></tr>
          <tr><td>401</td><td>Unauthorized &mdash; missing or invalid API key</td></tr>
          <tr><td>404</td><td>Not Found</td></tr>
          <tr><td>409</td><td>Conflict &mdash; resource already used</td></tr>
          <tr><td>429</td><td>Too Many Requests &mdash; rate limit exceeded</td></tr>
          <tr><td>500</td><td>Internal Server Error</td></tr>
        </tbody>
      </table>

      <p>Error response body:</p>

      <pre><code>{
  "error": {
    "code": "invalid_input",
    "message": "The 'ttl' field must be a positive integer",
    "details": {
      "field": "ttl",
      "provided": -1
    }
  }
}</code></pre>

      <h2>Rate Limiting</h2>

      <p>API requests are rate-limited per API key:</p>

      <table>
        <thead>
          <tr>
            <th>Tier</th>
            <th>Requests per minute</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>Free</td><td>60</td></tr>
          <tr><td>Pro</td><td>600</td></tr>
          <tr><td>Enterprise</td><td>6000</td></tr>
        </tbody>
      </table>

      <p>Rate limit headers are included in all responses:</p>

      <pre><code>X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1700000100</code></pre>
    </div>
  );
}
