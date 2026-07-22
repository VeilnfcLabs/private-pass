export default function RegistryPage() {
  return (
    <div>
      <h1>Decentralized Trust Registry</h1>
      <p>
        The VeilPass Trust Registry provides a decentralized framework for registering and
        verifying credential issuers using Decentralized Identifiers (DIDs). It enables anyone
        to verify that a credential was issued by a known and trusted entity without relying
        on a central certificate authority.
      </p>

      <h2>How It Works</h2>
      <ol>
        <li><strong>Issuer Registration:</strong> Issuers register their DID and public key in the trust registry.</li>
        <li><strong>Credential Issuance:</strong> When issuing credentials, the issuer includes their DID in the credential payload.</li>
        <li><strong>Verification:</strong> Verifiers check the registry to confirm the issuer DID is registered and the public key matches.</li>
        <li><strong>Revocation:</strong> Issuers can be de-registered or marked as untrusted.</li>
      </ol>

      <h2>API Endpoints</h2>
      <pre><code>POST /api/v1/registry              # Register an issuer
GET  /api/v1/registry              # List all registered issuers
GET  /api/v1/registry/{did}        # Look up an issuer by DID
POST /api/v1/registry/verify       # Verify a credential issuer</code></pre>

      <h3>Register Issuer</h3>
      <pre><code>POST /api/v1/registry
{
  "did": "did:veilpass:abc123def456",
  "name": "My Organization",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A..."
}</code></pre>

      <h3>Verify Credential Issuer</h3>
      <pre><code>POST /api/v1/registry/verify
{
  "credential": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9...",
  "issuer_did": "did:veilpass:abc123def456"
}</code></pre>

      <h2>CLI Usage</h2>
      <pre><code># Register an issuer
veil registry register --did "did:veilpass:abc123" --name "My Org" --key "public-key-pem"

# List all issuers
veil registry list

# Look up an issuer
veil registry lookup "did:veilpass:abc123"

# Verify a credential issuer
veil registry verify --issuer-did "did:veilpass:abc123"</code></pre>

      <h2>DID Format</h2>
      <p>
        VeilPass uses the <code>did:veilpass</code> DID method. The DID format is:
        <code>did:veilpass:&lt;base58-encoded-public-key-hash&gt;</code>
      </p>
    </div>
  );
}
