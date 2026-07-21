/**
 * VeilPass API — CommonJS example
 *
 * Run: node index.cjs
 */

const axios = require("axios");

const API_BASE = process.env.VEILPASS_API_URL || "http://localhost:8000";
const API_KEY = process.env.VEILPASS_API_KEY || "";

const client = axios.create({
  baseURL: API_BASE,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
  },
});

function log(label, data) {
  console.log(`\n── ${label} ──`);
  console.log(JSON.stringify(data, null, 2));
}

async function main() {
  try {
    // 1. QR Generation
    const qr = await client.post("/api/v1/qr", {
      content: "https://veilpass.app",
      format: "png",
      ecl: "H",
      size: 512,
      margin: 4,
      color: "#000000",
      bg_color: "#FFFFFF",
      include_logo: false,
      one_time: false,
      expires_in: null,
    }, { headers: { Accept: "application/json" } });
    log("QR Generation", qr.data);

    // 2. NFC Payload
    const nfc = await client.post("/api/v1/nfc", {
      issuer: "veilpass",
      payload: "https://veilpass.app/contact",
      version: "1.0",
      type: "uri",
      expiration: null,
      metadata: { department: "engineering" },
    });
    log("NFC Payload", nfc.data);

    // 3. Signed Link
    const link = await client.post("/api/v1/signed-link", {
      resource: "documents/nda-q3-2026.pdf",
      ttl: 86400,
      one_time: true,
      max_uses: 5,
    });
    log("Signed Link", link.data);

    // 4. Signed URL
    const signedUrl = await client.post("/api/v1/signed-url", {
      url: "https://storage.veilpass.app/reports/audit.pdf",
      permissions: "read",
      expires_in: 3600,
      download_limit: 10,
      one_time: false,
    });
    log("Signed URL", signedUrl.data);

    // 5. Token Generation
    const token = await client.post("/api/v1/token", {
      subject: "user_abc123",
      audience: "api.veilpass.app",
      issuer: "veilpass",
      expires_in: 86400,
      claims: { role: "admin", region: "us-east" },
    });
    log("Token", token.data);

    // 6. Verification
    const verify = await client.post("/api/v1/verify", {
      type: "token",
      value: token.data.token,
    });
    log("Verification", verify.data);

    console.log("\n✅ All API operations completed successfully.");
  } catch (err) {
    const msg = err.response?.data || err.message;
    console.error("\n❌ Error:", JSON.stringify(msg, null, 2));
    process.exit(1);
  }
}

main();
