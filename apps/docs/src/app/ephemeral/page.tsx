export default function EphemeralPage() {
  return (
    <div>
      <h1>Ephemeral Self-Destructing Credentials</h1>
      <p>
        Ephemeral credentials are short-lived, self-destructing tokens that automatically expire
        after a configurable time-to-live (TTL) and can optionally self-destruct after a single use.
        They are ideal for scenarios requiring temporary, auditable, and verifiable access.
      </p>

      <h2>Features</h2>
      <ul>
        <li><strong>Configurable TTL:</strong> Sub-minute to 24-hour lifespans.</li>
        <li><strong>One-Time Auto-Destruction:</strong> Credentials can be configured to self-destruct after first verification.</li>
        <li><strong>HMAC-Signed:</strong> Each credential is cryptographically signed to prevent tampering.</li>
        <li><strong>Prefix Convention:</strong> Tokens use <code>ep_</code> prefix for easy identification (<code>ep_ot_</code> for one-time tokens).</li>
      </ul>

      <h2>API Endpoints</h2>
      <pre><code>POST /api/v1/ephemeral          # Create an ephemeral credential
POST /api/v1/ephemeral/verify   # Verify and optionally consume a credential</code></pre>

      <h3>Create Ephemeral Credential</h3>
      <pre><code>POST /api/v1/ephemeral
{
  "content": "sensitive-access-data",
  "ttl": 600,
  "one_time": true
}</code></pre>

      <h3>Verify Ephemeral Credential</h3>
      <pre><code>POST /api/v1/ephemeral/verify
{
  "token": "ep_ot_c2Vuc2l0aXZlLXBhc3N3b3Jk.1700003600.sig123"
}</code></pre>

      <h2>TTL Presets</h2>
      <table>
        <thead>
          <tr><th>Preset</th><th>Duration</th><th>Use Case</th></tr>
        </thead>
        <tbody>
          <tr><td>5 Minutes</td><td>300s</td><td>Emergency access, password reset</td></tr>
          <tr><td>10 Minutes</td><td>600s</td><td>One-time document access</td></tr>
          <tr><td>30 Minutes</td><td>1800s</td><td>Conference room booking</td></tr>
          <tr><td>1 Hour</td><td>3600s</td><td>API temporary access</td></tr>
          <tr><td>24 Hours</td><td>86400s</td><td>Day pass / event access</td></tr>
        </tbody>
      </table>

      <h2>CLI Usage</h2>
      <pre><code># Create a one-time 10-minute credential
veil ephemeral create --content "door-access-7" --ttl 10m --one-time

# Create a 24-hour credential
veil ephemeral create --content "event-pass-2026" --ttl 24h

# Verify a credential
veil ephemeral verify ep_ot_c2Vuc2l0aXZl.1700003600.sig123</code></pre>
    </div>
  );
}
