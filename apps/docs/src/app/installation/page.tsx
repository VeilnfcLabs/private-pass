export default function InstallationPage() {
  return (
    <div>
      <h1>Installation</h1>

      <p>
        VeilPass can be installed through multiple package managers and platforms.
        Choose the method that works best for your environment.
      </p>

      <h2>npm (Node.js)</h2>

      <p>Install the CLI globally using npm:</p>

      <pre><code>npm install -g veilpass-cli</code></pre>

      <p>Or run it directly without installing:</p>

      <pre><code>npx veilpass-cli qr "Hello, VeilPass"</code></pre>

      <p>Verify the installation:</p>

      <pre><code>veil --version
veil --help</code></pre>

      <h2>Cargo (Rust)</h2>

      <p>If you prefer the Rust-native build, install via Cargo:</p>

      <pre><code>cargo install veilpass-cli</code></pre>

      <p>This compiles a standalone binary with no runtime dependencies.</p>

      <pre><code>veil qr "Hello, VeilPass" --format utf8</code></pre>

      <h2>Docker</h2>

      <p>Pull the official Docker image:</p>

      <pre><code>docker pull veilpass/veilpass-cli:latest</code></pre>

      <p>Run commands inside the container:</p>

      <pre><code>docker run --rm veilpass/veilpass-cli veil qr "Hello, VeilPass"</code></pre>

      <p>To save output files to your host, mount a volume:</p>

      <pre><code>docker run --rm -v $(pwd):/output veilpass/veilpass-cli \
  veil qr "Hello, VeilPass" --format png -o /output/qr.png</code></pre>

      <h2>Homebrew (macOS / Linux)</h2>

      <p>Add the VeilPass tap and install:</p>

      <pre><code>brew tap veilpass/tap
brew install veilpass-cli</code></pre>

      <p>Update an existing installation:</p>

      <pre><code>brew upgrade veilpass-cli</code></pre>

      <h2>Build from Source</h2>

      <p>Clone the repository and build with Node.js:</p>

      <pre><code>git clone https://github.com/veilpass/veilpass.git
cd veilpass/cli
npm install
npm run build
npm link</code></pre>

      <p>Verify the build:</p>

      <pre><code>veil --version
# Output: 0.1.0</code></pre>

      <h2>System Requirements</h2>

      <table>
        <thead>
          <tr>
            <th>Dependency</th>
            <th>Minimum Version</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Node.js</td>
            <td>18.x</td>
            <td>Required for npm installation</td>
          </tr>
          <tr>
            <td>Rust (optional)</td>
            <td>1.70</td>
            <td>Required for Cargo installation</td>
          </tr>
          <tr>
            <td>Docker (optional)</td>
            <td>24.x</td>
            <td>Required for Docker installation</td>
          </tr>
        </tbody>
      </table>

      <h2>Configuration</h2>

      <p>After installation, configure the CLI with your API endpoint:</p>

      <pre><code>veil config set api-url https://api.veilpass.io
veil config set algorithm HS256
veil config set output-format json</code></pre>

      <p>View your current configuration:</p>

      <pre><code>veil config list</code></pre>

      <div className="callout callout-info">
        The default API URL is <code>http://localhost:8000</code>. Change it to point to
        your production VeilPass server.
      </div>
    </div>
  );
}
