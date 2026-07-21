export default function QuickStartPage() {
  return (
    <div>
      <h1>Quick Start</h1>

      <p>
        Get started with VeilPass in under five minutes. This guide walks you through generating
        your first QR code, creating a signed token, and verifying it.
      </p>

      <h2>1. Install the CLI</h2>

      <pre><code>npm install -g veilpass-cli</code></pre>

      <p>Verify it installed correctly:</p>

      <pre><code>veil --version
# Output: 0.1.0</code></pre>

      <h2>2. Generate a QR Code</h2>

      <p>Create a QR code that encodes a URL. Display it in the terminal:</p>

      <pre><code>veil qr "https://veilpass.io/claim/abc123" --format terminal</code></pre>

      <p>Save it as a PNG image:</p>

      <pre><code>veil qr "https://veilpass.io/claim/abc123" --format png -o ./qr.png</code></pre>

      <p>Create a QR code that expires in 5 minutes and can only be used once:</p>

      <pre><code>veil qr "https://veilpass.io/claim/abc123" \
  --format png \
  --expires-in 300 \
  --one-time \
  -o ./secure-qr.png</code></pre>

      <h2>3. Create a JWT Token</h2>

      <pre><code>veil token create \
  --sub user_123 \
  --aud veilpass-api \
  --iss veilpass-cli \
  --ttl 3600</code></pre>

      <p>This outputs a JWT token valid for one hour. The token contains standard claims
      (subject, audience, issuer, issued-at, expiration) and a unique JWT ID.</p>

      <h2>4. Decode and Verify a Token</h2>

      <p>Decode a token to inspect its contents:</p>

      <pre><code>veil decode &lt;your-token&gt;</code></pre>

      <p>This shows the header, payload, and signature preview.</p>

      <p>Verify the token:</p>

      <pre><code>veil verify token &lt;your-token&gt;</code></pre>

      <p>The output shows whether the token is valid, expired, and includes the issuer, subject, and audience.</p>

      <h2>5. Generate an NFC Payload</h2>

      <p>Create an NFC payload for physical access:</p>

      <pre><code>veil nfc \
  --type uri \
  --payload "https://veilpass.io/claim/door-42" \
  --issuer "Building-A" \
  --format json</code></pre>

      <p>Export as NDEF format for writing to an NFC tag:</p>

      <pre><code>veil nfc --type text --payload "access-granted" --format ndef -o ./tag.ndef</code></pre>

      <h2>6. Sign a URL</h2>

      <p>Add cryptographic signatures to URLs for secure sharing:</p>

      <pre><code>veil sign url "https://api.veilpass.io/documents/report.pdf" \
  --ttl 86400 \
  --permissions "read,download"</code></pre>

      <h2>7. Generate a Secure Claim Link</h2>

      <p>Create a one-time claim link for secure resource access:</p>

      <pre><code>veil link create "resource:doc-42" \
  --ttl 3600 \
  --one-time \
  --max-uses 1</code></pre>

      <p>Verify a claim link:</p>

      <pre><code>veil link verify "https://veilpass.io/claim?r=resource:doc-42&exp=...&s=..."</code></pre>

      <h2>8. Manage Keys</h2>

      <p>Initialize a key pair for signing:</p>

      <pre><code>veil key init</code></pre>

      <p>List existing keys:</p>

      <pre><code>veil key list</code></pre>

      <p>Export a public key:</p>

      <pre><code>veil key export ./public.pem --public-only --key-id vk-abc123</code></pre>

      <h2>Next Steps</h2>

      <ul>
        <li>Read the full <a href="/cli">CLI Reference</a> for all commands and options.</li>
        <li>Integrate with the <a href="/api">REST API</a> for server-side verification.</li>
        <li>Use the <a href="/sdk">SDK</a> to embed authentication in your apps.</li>
      </ul>
    </div>
  );
}
