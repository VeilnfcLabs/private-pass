export default function SdJwtPage() {
  return (
    <div>
      <h1>Selective Disclosure (SD-JWT)</h1>
      <p>
        SD-JWT (Selective Disclosure JWT) is an extension of the JWT standard that allows issuers to
        create tokens where the holder can selectively reveal only a subset of claims to verifiers.
        This is achieved by salting and hashing each claim individually, then including only the
        digests in the signed token body.
      </p>

      <h2>How It Works</h2>
      <ol>
        <li><strong>Issuance:</strong> The issuer takes a set of claims, generates a random salt per claim, computes <code>SHA-256(salt + claim_value)</code> for each, and signs the JWT containing only the salted digests.</li>
        <li><strong>Disclosures:</strong> The issuer sends the holder the full set of <code>(salt, claim_value)</code> pairs as disclosures alongside the SD-JWT.</li>
        <li><strong>Presentation:</strong> The holder selects which claims to reveal and sends the SD-JWT plus only the corresponding disclosures to the verifier.</li>
        <li><strong>Verification:</strong> The verifier checks that the digest of each presented disclosure matches the digest in the SD-JWT, and verifies the JWT signature.</li>
      </ol>

      <h2>API Endpoints</h2>
      <pre><code>POST /api/v1/token/sd-jwt           # Create an SD-JWT
POST /api/v1/token/sd-jwt/present   # Create a presentation (select disclosures)
POST /api/v1/verify/sd-jwt          # Verify an SD-JWT presentation</code></pre>

      <h3>Create SD-JWT</h3>
      <pre><code>POST /api/v1/token/sd-jwt
{
  "claims": {
    "sub": "user_42",
    "email": "user@example.com",
    "role": "admin",
    "department": "engineering"
  },
  "issuer": "VeilPass"
}</code></pre>

      <h3>Present Selected Claims</h3>
      <pre><code>POST /api/v1/token/sd-jwt/present
{
  "sd_jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6InNkK2p3dCJ9...",
  "disclosures_to_reveal": ["email", "role"]
}</code></pre>

      <h2>Use Cases</h2>
      <ul>
        <li><strong>Identity Verification:</strong> Prove you are over 18 without revealing your exact birth date.</li>
        <li><strong>Access Control:</strong> Show you belong to a group without revealing your user ID.</li>
        <li><strong>Privacy Compliance:</strong> Reveal only the minimum necessary data (GDPR Article 5).</li>
      </ul>
    </div>
  );
}
