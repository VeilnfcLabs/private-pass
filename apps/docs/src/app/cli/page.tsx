export default function CliPage() {
  return (
    <div>
      <h1>CLI Reference</h1>

      <p>
        The <code>veil</code> CLI tool provides a complete interface for generating QR codes, NFC payloads,
        tokens, signed links, and managing keys and configuration. It can be invoked as either
        <code>veil</code> or <code>veilpass</code>.
      </p>

      <h2>Global Options</h2>

      <pre><code>veil [command] [options]

Global options:
  -V, --version   output the version number
  -h, --help      display help for command</code></pre>

      <h2>veil qr — Generate QR Codes</h2>

      <p>Generate QR codes in multiple formats with configurable appearance and metadata.</p>

      <pre><code>veil qr [options] &lt;content&gt;

Arguments:
  content                   Content to encode in the QR code

Options:
  -f, --format &lt;format&gt;     Output format (terminal, png, svg, utf8) (default: "terminal")
  --ecl &lt;level&gt;             Error correction level (L, M, Q, H) (default: "M")
  --size &lt;size&gt;             QR code size in pixels (default: "256")
  --margin &lt;margin&gt;         Margin around QR code (default: "4")
  -o, --output &lt;path&gt;       Output file path
  --color &lt;color&gt;           Foreground color (hex) (default: "#000000")
  --bg-color &lt;color&gt;        Background color (hex) (default: "#ffffff")
  --expires-in &lt;seconds&gt;    Expiration time in seconds
  --one-time                Mark as one-time use
  -h, --help                display help for command</code></pre>

      <p>Examples:</p>

      <pre><code># Display in terminal
veil qr "https://example.com"

# Save as PNG
veil qr "https://example.com" --format png -o qr.png

# Custom colors and high error correction
veil qr "https://example.com" --format png --color "#6366f1" --bg-color "#0f172a" --ecl H -o branded-qr.png

# With expiry and one-time use
veil qr "secret-data" --expires-in 300 --one-time --format utf8</code></pre>

      <h2>veil nfc — Generate NFC Payloads</h2>

      <p>Create NFC payloads in multiple formats for writing to NFC tags.</p>

      <pre><code>veil nfc [options]

Options:
  -t, --type &lt;type&gt;         NFC record type (text, uri, smartposter, app) (default: "text")
  -p, --payload &lt;payload&gt;   Payload content
  -i, --issuer &lt;issuer&gt;     Issuer identifier
  --version &lt;version&gt;       Payload version (default: "1.0")
  -o, --output &lt;path&gt;       Output file path
  -f, --format &lt;format&gt;     Output format (json, hex, base64, ndef) (default: "json")
  -h, --help                display help for command</code></pre>

      <p>Examples:</p>

      <pre><code># JSON format
veil nfc --type uri --payload "https://veilpass.io/auth" --issuer "office-door"

# NDEF format for tag writing
veil nfc --type text --payload "access-granted" --format ndef -o tag.ndef

# Base64 encoded
veil nfc --type app --payload "com.veilpass.auth" --format base64</code></pre>

      <h2>veil link — Secure Claim Links</h2>

      <p>Create and verify cryptographically signed claim links.</p>

      <pre><code>veil link create [options] &lt;resource&gt;
veil link verify &lt;url&gt;

Create options:
  --ttl &lt;seconds&gt;           Time-to-live in seconds (default: "3600")
  --one-time                One-time use link
  --max-uses &lt;count&gt;        Maximum number of uses (default: "1")</code></pre>

      <p>Examples:</p>

      <pre><code># Create a one-time link valid for 1 hour
veil link create "resource:doc-42" --ttl 3600 --one-time

# Create a multi-use link valid for 24 hours
veil link create "resource:door-7" --ttl 86400 --max-uses 100

# Verify a claim link
veil link verify "https://veilpass.io/claim?r=resource:doc-42&exp=1700000000&s=sig_abc123"</code></pre>

      <h2>veil sign — Sign URLs and Messages</h2>

      <p>Cryptographically sign URLs and messages with key identifiers and permission scopes.</p>

      <pre><code>veil sign url &lt;url&gt; [options]
veil sign message &lt;message&gt; [options]

Options:
  --ttl &lt;seconds&gt;           Time-to-live in seconds (default: "3600")
  --key-id &lt;id&gt;             Key identifier (default: "default")
  --permissions &lt;perms&gt;     Comma-separated permissions (default: "read")</code></pre>

      <p>Examples:</p>

      <pre><code># Sign a download URL valid for 24 hours
veil sign url "https://api.veilpass.io/files/report.pdf" --ttl 86400

# Sign with specific permissions
veil sign url "https://api.veilpass.io/admin" --ttl 300 --permissions "read,write"

# Sign a message
veil sign message "{\"action\": \"deploy\", \"env\": \"production\"}" --key-id deploy-key</code></pre>

      <h2>veil token — Create and Decode Tokens</h2>

      <p>Create time-limited JWT tokens and decode existing tokens.</p>

      <pre><code>veil token create [options]
veil token decode &lt;token&gt;

Create options:
  --sub &lt;subject&gt;           Token subject (default: "user")
  --aud &lt;audience&gt;          Token audience (default: "veilpass-api")
  --iss &lt;issuer&gt;            Token issuer (default: "veilpass-cli")
  --ttl &lt;seconds&gt;           Time-to-live in seconds (default: "3600")
  --claims &lt;json&gt;           Additional claims as JSON string</code></pre>

      <p>Examples:</p>

      <pre><code># Create a standard token
veil token create --sub user_42 --aud my-api --iss my-app --ttl 3600

# Create a token with custom claims
veil token create --sub admin --ttl 600 --claims '{"role": "admin", "department": "eng"}'

# Decode a token
veil token decode eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...</code></pre>

      <h2>veil verify — Verify Credentials</h2>

      <p>Verify tokens, links, signed URLs, and cryptographic signatures.</p>

      <pre><code>veil verify &lt;type&gt; &lt;value&gt;

Types:
  token       Verify a JWT token
  link        Verify a claim link URL
  url         Verify a signed URL
  signature   Verify a cryptographic signature</code></pre>

      <p>Examples:</p>

      <pre><code># Verify a token
veil verify token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Verify a claim link
veil verify link "https://veilpass.io/claim?r=resource&exp=1700000000&s=sig_abc"

# Verify a signed URL
veil verify url "https://api.veilpass.io/data?sig=abc123&exp=1700000000"

# Verify a signature string
veil verify signature "signature: abc123def456..."</code></pre>

      <h2>veil decode — Decode JWT Tokens</h2>

      <p>Decode a JWT token without verification to inspect its header and payload.</p>

      <pre><code>veil decode &lt;token&gt;

Arguments:
  token  JWT token to decode</code></pre>

      <p>Example:</p>

      <pre><code>veil decode eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature</code></pre>

      <p>Output shows the decoded header, payload, signature preview, and metadata like expiration status.</p>

      <h2>veil key — Key Management</h2>

      <p>Generate, list, export, import, and inspect cryptographic keys.</p>

      <pre><code>veil key init
veil key list
veil key export &lt;path&gt; [options]
veil key import &lt;path&gt; [options]
veil key info [options]

Export options:
  --key-id &lt;id&gt;            Key ID to export
  --public-only            Export only the public key

Import options:
  --key-id &lt;id&gt;            Assign a specific key ID

Info options:
  --key-id &lt;id&gt;            Key ID to inspect</code></pre>

      <p>Examples:</p>

      <pre><code># Generate a new RSA key pair
veil key init

# List all keys
veil key list

# Export public key
veil key export ./public.pem --public-only --key-id vk-abc123

# Import an existing key
veil key import ./my-key.pem --key-id my-custom-key

# Show key details
veil key info</code></pre>

      <h2>veil config — Configuration Management</h2>

      <p>Manage CLI configuration settings.</p>

      <pre><code>veil config set &lt;key&gt; &lt;value&gt;
veil config get &lt;key&gt;
veil config list

Configuration keys:
  api-url          API base URL (default: http://localhost:8000)
  default-ttl      Default token TTL in seconds (default: 3600)
  algorithm        Signing algorithm (HS256, HS384, HS512, RS256, RS384, RS512)
  output-format    Output format (text, json, table)</code></pre>

      <p>Examples:</p>

      <pre><code># Set API URL
veil config set api-url https://api.veilpass.io

# Set default TTL to 1 hour
veil config set default-ttl 3600

# Set signing algorithm
veil config set algorithm RS256

# Set output format
veil config set output-format json

# Get a specific value
veil config get api-url

# List all configuration
veil config list</code></pre>

      <h2>Aliases</h2>

      <p>The CLI can be invoked using either name:</p>

      <pre><code>veil qr "content"     # preferred
veilpass qr "content"  # alias</code></pre>

      <p>Both commands behave identically.</p>
    </div>
  );
}
