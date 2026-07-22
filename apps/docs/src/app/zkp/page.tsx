export default function ZkpPage() {
  return (
    <div>
      <h1>Zero-Knowledge Proof Authentication</h1>
      <p>
        VeilPass implements a Schnorr-based zero-knowledge proof protocol that allows a prover
        to demonstrate knowledge of a secret without revealing the secret itself. The protocol
        uses a 2048-bit safe prime group (RFC 3526 Group 14) and the Fiat-Shamir heuristic for
        non-interactive proof generation.
      </p>

      <h2>How It Works</h2>
      <ol>
        <li><strong>Setup:</strong> A safe prime <code>p = 2q + 1</code> is used, where both <code>p</code> and <code>q</code> are prime. A generator <code>g</code> of the subgroup of order <code>q</code> is chosen.</li>
        <li><strong>Key Generation:</strong> The prover chooses a secret <code>x</code> (private key) and computes <code>y = g^x mod p</code> (public key).</li>
        <li><strong>Commitment:</strong> The prover picks a random <code>r</code>, computes <code>t = g^r mod p</code>, and sends <code>t</code> to the verifier.</li>
        <li><strong>Challenge:</strong> The verifier sends a random challenge <code>c</code> (or it is derived via Fiat-Shamir: <code>c = Hash(g || y || t)</code>).</li>
        <li><strong>Response:</strong> The prover computes <code>s = r + c*x mod q</code> and sends <code>s</code> to the verifier.</li>
        <li><strong>Verification:</strong> The verifier checks <code>g^s = t * y^c mod p</code>. If equal, the proof is valid.</li>
      </ol>

      <h2>API Endpoints</h2>
      <pre><code>POST /api/v1/zkp/keypair  # Generate a ZKP keypair
POST /api/v1/zkp/proof    # Generate a proof
POST /api/v1/zkp/verify   # Verify a proof</code></pre>

      <h3>Generate Keypair</h3>
      <pre><code>POST /api/v1/zkp/keypair
{
  "secret": "user-supplied-secret"
}</code></pre>

      <h3>Generate Proof</h3>
      <pre><code>POST /api/v1/zkp/proof
{
  "secret": "user-supplied-secret",
  "public_key": "generated-public-key"
}</code></pre>

      <h2>Security Properties</h2>
      <ul>
        <li><strong>Completeness:</strong> An honest prover always convinces an honest verifier.</li>
        <li><strong>Soundness:</strong> A cheating prover cannot convince the verifier (except with negligible probability).</li>
        <li><strong>Zero-Knowledge:</strong> The verifier learns nothing about the secret, only that the prover knows it.</li>
        <li><strong>Replay Protection:</strong> Timestamps are embedded in the proof to prevent replay attacks.</li>
      </ul>
    </div>
  );
}
