/**
 * VeilPass API — ESM (ECMAScript Module) example
 *
 * Demonstrates all 6 API operations using axios.
 * Run: node index.js
 *
 * API base URL is configurable via VEILPASS_API_URL env var.
 */

import axios from "axios";
import { strict as assert } from "node:assert";

// ── Configuration ──────────────────────────────────────────────────────────────

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

// ── Helper: pretty-print responses ──────────────────────────────────────────────

function log(label, data) {
  console.log(`\n── ${label} ──`);
  console.log(JSON.stringify(data, null, 2));
}

// ── 1. QR Generation ────────────────────────────────────────────────────────────

async function generateQR() {
  const res = await client.post("/api/v1/qr", {
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
  }, {
    headers: { Accept: "application/json" },
  });

  log("QR Generation", res.data);
  return res.data;
}

// ── 2. NFC Payload ──────────────────────────────────────────────────────────────

async function generateNFC() {
  const res = await client.post("/api/v1/nfc", {
    issuer: "veilpass",
    payload: "https://veilpass.app/contact",
    version: "1.0",
    type: "uri",
    expiration: null,
    metadata: { department: "engineering" },
  });

  log("NFC Payload", res.data);
  return res.data;
}

// ── 3. Signed Link ─────────────────────────────────────────────────────────────

async function createSignedLink() {
  const res = await client.post("/api/v1/signed-link", {
    resource: "documents/nda-q3-2026.pdf",
    ttl: 86400,
    one_time: true,
    max_uses: 5,
  });

  log("Signed Link", res.data);
  return res.data;
}

// ── 4. Signed URL ──────────────────────────────────────────────────────────────

async function createSignedURL() {
  const res = await client.post("/api/v1/signed-url", {
    url: "https://storage.veilpass.app/reports/audit.pdf",
    permissions: "read",
    expires_in: 3600,
    download_limit: 10,
    one_time: false,
  });

  log("Signed URL", res.data);
  return res.data;
}

// ── 5. Token Generation ────────────────────────────────────────────────────────

async function generateToken() {
  const res = await client.post("/api/v1/token", {
    subject: "user_abc123",
    audience: "api.veilpass.app",
    issuer: "veilpass",
    expires_in: 86400,
    claims: { role: "admin", region: "us-east" },
  });

  log("Token", res.data);
  return res.data;
}

// ── 6. Verification ─────────────────────────────────────────────────────────────

async function verifyToken(token) {
  const res = await client.post("/api/v1/verify", {
    type: "token",
    value: token,
  });

  log("Verification", res.data);
  return res.data;
}

// ── Main ────────────────────────────────────────────────────────────────────────

async function main() {
  try {
    const qr = await generateQR();
    assert(qr.success, "QR generation failed");

    const nfc = await generateNFC();
    assert(nfc.success, "NFC generation failed");

    const link = await createSignedLink();
    assert(link.success, "Signed link creation failed");

    const signedUrl = await createSignedURL();
    assert(signedUrl.success, "Signed URL creation failed");

    const token = await generateToken();
    assert(token.success, "Token generation failed");

    const verification = await verifyToken(token.token);
    assert(verification.valid, "Token verification failed");

    console.log("\n✅ All API operations completed successfully.");
  } catch (err) {
    const msg = err.response?.data || err.message;
    console.error("\n❌ Error:", JSON.stringify(msg, null, 2));
    process.exit(1);
  }
}

main();
