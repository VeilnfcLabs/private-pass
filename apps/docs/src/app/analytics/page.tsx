export default function AnalyticsPage() {
  return (
    <div>
      <h1>Privacy-First QR Analytics</h1>
      <p>
        VeilPass provides privacy-first scan analytics that respect user privacy while still
        delivering actionable insights. The analytics system supports three privacy modes and
        is compliant with GDPR and the Kenya Data Protection Act.
      </p>

      <h2>Privacy Modes</h2>
      <table>
        <thead>
          <tr><th>Mode</th><th>Data Collected</th><th>Use Case</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Standard</strong></td>
            <td>IP address, user agent, referrer, location (country/city), timestamp</td>
            <td>Internal enterprise analytics with consent</td>
          </tr>
          <tr>
            <td><strong>Privacy</strong></td>
            <td>Country-level location only, user agent family, referrer domain</td>
            <td>Public-facing QR campaigns</td>
          </tr>
          <tr>
            <td><strong>Aggregate Only</strong></td>
            <td>Total scan count only, no individual data</td>
            <td>Maximum privacy compliance</td>
          </tr>
        </tbody>
      </table>

      <h2>API Endpoints</h2>
      <pre><code>POST /api/v1/dynamic-qr                # Create a dynamic QR code
GET  /api/v1/r/{code}                  # Redirect endpoint (tracks scan)
GET  /api/v1/dynamic-qr/{id}/analytics # Get analytics for a QR code
GET  /api/v1/dynamic-qr/{id}/privacy-score # Get privacy compliance score</code></pre>

      <h3>Create Dynamic QR with Privacy Mode</h3>
      <pre><code>POST /api/v1/dynamic-qr
{
  "destination_url": "https://example.com",
  "privacy_mode": "privacy",
  "title": "Campaign QR"
}</code></pre>

      <h3>Get Analytics</h3>
      <pre><code>GET /api/v1/dynamic-qr/{id}/analytics
Response:
{
  "total_scans": 12847,
  "unique_ips": 3421,
  "scans_over_time": [...],
  "top_agents": [...],
  "top_referrers": [...],
  "privacy_mode": "privacy"
}</code></pre>

      <h2>Compliance</h2>
      <ul>
        <li><strong>GDPR:</strong> Privacy and Aggregate Only modes comply with GDPR Article 5 (data minimization).</li>
        <li><strong>Kenya DPA:</strong> Compliance with Section 25 (data minimization) and Section 26 (purpose limitation).</li>
        <li><strong>Differential Privacy:</strong> Geographic data is rounded to city/country level in Privacy mode.</li>
        <li><strong>Auto-Delete:</strong> Scan data is automatically deleted after the configured retention period.</li>
      </ul>
    </div>
  );
}
