export default function SdkPage() {
  return (
    <div>
      <h1>SDK Documentation</h1>

      <p>
        VeilPass provides client SDKs for multiple programming languages. These SDKs wrap the REST API
        and provide idiomatic interfaces for generating QR codes, tokens, signed links, and more.
      </p>

      <h2>JavaScript / TypeScript SDK</h2>

      <p>Install the SDK via npm:</p>

      <pre><code>npm install @veilpass/sdk</code></pre>

      <p>Basic usage:</p>

      <pre><code>import { VeilPassClient } from '@veilpass/sdk';

const client = new VeilPassClient({
  apiKey: 'vp_api_abc123',
  baseURL: 'https://api.veilpass.io',
});

// Generate a QR code
const qr = await client.qr.create({
  content: 'https://example.com/claim/abc',
  options: { format: 'png', width: 512 },
});
console.log(qr.qr_code); // data:image/png;base64,...

// Create a token
const token = await client.tokens.create({
  sub: 'user_42',
  aud: 'my-api',
  ttl: 3600,
  claims: { role: 'admin' },
});
console.log(token.token);

// Verify a token
const verification = await client.tokens.verify(token.token);
console.log(verification.valid); // true

// Create a claim link
const link = await client.links.create({
  resource: 'resource:doc-42',
  ttl: 86400,
  one_time: true,
});
console.log(link.url);

// Sign a message
const signature = await client.sign.create({
  data: 'message-to-sign',
  keyId: 'vk-abc123',
});
console.log(signature.signature);</code></pre>

      <h3>Error Handling</h3>

      <pre><code>import { VeilPassError } from '@veilpass/sdk';

try {
  await client.tokens.create({ sub: '', ttl: -1 });
} catch (error) {
  if (error instanceof VeilPassError) {
    console.error(error.status, error.message, error.details);
  }
}</code></pre>

      <h2>Python SDK</h2>

      <p>Install via pip:</p>

      <pre><code>pip install veilpass-sdk</code></pre>

      <p>Basic usage:</p>

      <pre><code>from veilpass import VeilPassClient

client = VeilPassClient(
    api_key="vp_api_abc123",
    base_url="https://api.veilpass.io"
)

# Generate a QR code
qr = client.qr.create(
    content="https://example.com/claim/abc",
    options={"format": "png", "width": 512}
)
print(qr.qr_code)

# Create a token
token = client.tokens.create(
    sub="user_42",
    aud="my-api",
    ttl=3600,
    claims={"role": "admin"}
)
print(token.token)

# Verify a token
verification = client.tokens.verify(token.token)
print(verification.valid)

# Create a claim link
link = client.links.create(
    resource="resource:doc-42",
    ttl=86400,
    one_time=True
)
print(link.url)

# Sign a message
sig = client.sign.create(
    data="message-to-sign",
    key_id="vk-abc123"
)
print(sig.signature)</code></pre>

      <h2>Rust SDK</h2>

      <p>Add to your <code>Cargo.toml</code>:</p>

      <pre><code>[dependencies]
veilpass-sdk = "0.1"</code></pre>

      <p>Basic usage:</p>

      <pre><code>use veilpass_sdk::{VeilPassClient, QrOptions};

#[tokio::main]
async fn main() {
    let client = VeilPassClient::new(
        "vp_api_abc123",
        "https://api.veilpass.io",
    );

    // Generate a QR code
    let qr = client.qr().create(
        "https://example.com/claim/abc",
        QrOptions { format: "png".into(), width: 512 },
    ).await.unwrap();
    println!("{}", qr.qr_code);

    // Create a token
    let token = client.tokens().create(
        "user_42",
        3600,
    ).await.unwrap();
    println!("{}", token.token);
}</code></pre>

      <h2>Go SDK</h2>

      <p>Install:</p>

      <pre><code>go get github.com/veilpass/sdk-go</code></pre>

      <p>Basic usage:</p>

      <pre><code>package main

import (
    "fmt"
    veilpass "github.com/veilpass/sdk-go"
)

func main() {
    client := veilpass.NewClient(
        "vp_api_abc123",
        "https://api.veilpass.io",
    )

    // Generate a QR code
    qr, _ := client.QR.Create("https://example.com/claim/abc", veilpass.QROptions{
        Format: "png",
        Width:  512,
    })
    fmt.Println(qr.QRCode)

    // Create a token
    token, _ := client.Tokens.Create("user_42", 3600, nil)
    fmt.Println(token.Token)

    // Create a claim link
    link, _ := client.Links.Create("resource:doc-42", 86400, true, 1)
    fmt.Println(link.URL)
}</code></pre>

      <h2>Java SDK</h2>

      <p>Add to your <code>pom.xml</code>:</p>

      <pre><code>&lt;dependency&gt;
    &lt;groupId&gt;io.veilpass&lt;/groupId&gt;
    &lt;artifactId&gt;veilpass-sdk&lt;/artifactId&gt;
    &lt;version&gt;0.1.0&lt;/version&gt;
&lt;/dependency&gt;</code></pre>

      <p>Basic usage:</p>

      <pre><code>import io.veilpass.*;

VeilPassClient client = new VeilPassClient(
    "vp_api_abc123",
    "https://api.veilpass.io"
);

// Generate a QR code
QRResult qr = client.qr().create(
    "https://example.com/claim/abc",
    new QROptions().format("png").width(512)
);
System.out.println(qr.getQRCode());

// Create a token
TokenResult token = client.tokens().create("user_42", 3600);
System.out.println(token.getToken());

// Verify a token
VerificationResult v = client.tokens().verify(token.getToken());
System.out.println(v.isValid());</code></pre>

      <h2>Client Configuration</h2>

      <p>All SDKs support the following configuration options:</p>

      <table>
        <thead>
          <tr>
            <th>Option</th>
            <th>Type</th>
            <th>Default</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>apiKey</code></td>
            <td>string</td>
            <td>&mdash;</td>
            <td>API key for authentication</td>
          </tr>
          <tr>
            <td><code>baseURL</code></td>
            <td>string</td>
            <td><code>http://localhost:8000</code></td>
            <td>API base URL</td>
          </tr>
          <tr>
            <td><code>timeout</code></td>
            <td>number</td>
            <td><code>10000</code></td>
            <td>Request timeout in milliseconds</td>
          </tr>
          <tr>
            <td><code>retries</code></td>
            <td>number</td>
            <td><code>3</code></td>
            <td>Number of retry attempts on failure</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
