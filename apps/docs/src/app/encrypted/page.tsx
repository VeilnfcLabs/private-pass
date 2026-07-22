export default function EncryptedPage() {
  return (
    <div>
      <h1>Hybrid NFC+QR Encrypted Payloads</h1>
      <p>
        VeilPass supports AES-256-GCM encryption that encrypts a payload once and produces
        both QR code and NFC NDEF outputs. This enables physical delivery of encrypted data
        through both visual (QR) and wireless (NFC) channels using the same decryption key.
      </p>

      <h2>How It Works</h2>
      <ol>
        <li><strong>Key Derivation:</strong> A user-chosen password is run through SHA-256 to derive a 256-bit AES key.</li>
        <li><strong>Encryption:</strong> The plaintext is encrypted using AES-256-GCM with a random 12-byte nonce. GCM provides authenticated encryption (confidentiality + integrity).</li>
        <li><strong>Dual Output:</strong> The same ciphertext is formatted into both a QR-compatible payload and an NFC NDEF record.</li>
        <li><strong>Decryption:</strong> The recipient scans either the QR code or taps the NFC tag, then enters the password to decrypt.</li>
      </ol>

      <h2>API Endpoints</h2>
      <pre><code>POST /api/v1/encrypted          # Encrypt content for QR + NFC
POST /api/v1/encrypted/decrypt  # Decrypt ciphertext</code></pre>

      <h3>Encrypt</h3>
      <pre><code>POST /api/v1/encrypted
{
  "content": "sensitive-data-to-protect",
  "password": "user-chosen-password"
}</code></pre>

      <h3>Decrypt</h3>
      <pre><code>POST /api/v1/encrypted/decrypt
{
  "ciphertext": "aes-256-gcm-ciphertext-hex",
  "password": "user-chosen-password",
  "nonce": "12-byte-nonce-hex",
  "tag": "16-byte-auth-tag-hex"
}</code></pre>

      <h2>Security Properties</h2>
      <ul>
        <li><strong>AES-256-GCM:</strong> Industry-standard authenticated encryption.</li>
        <li><strong>Random Nonce:</strong> A new random nonce is generated for every encryption.</li>
        <li><strong>Authentication Tag:</strong> GCM produces a 16-byte tag that detects tampering.</li>
        <li><strong>Password-Based KDF:</strong> SHA-256 key derivation means the same password always produces the same key.</li>
        <li><strong>No Key Storage:</strong> The encryption key is never stored on the server.</li>
      </ul>

      <h2>CLI Usage</h2>
      <pre><code># Encrypt content
veil encrypt create --content "my-secret-data" --password "strong-password"

# Decrypt content
veil encrypt decrypt --ciphertext "abc123..." --password "strong-password" --nonce "def456..." --tag "789012..."</code></pre>
    </div>
  );
}
