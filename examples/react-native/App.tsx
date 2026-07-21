/**
 * VeilPass API — React Native example
 *
 * Demonstrates all 6 API operations in a simple React Native app.
 * Run: npx expo start
 */

import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import axios from "axios";

// ── Configuration ──────────────────────────────────────────────────────────────

const API_BASE = "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE,
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
});

// ── Types ──────────────────────────────────────────────────────────────────────

interface ApiResult {
  label: string;
  data: Record<string, unknown>;
}

// ── App Component ──────────────────────────────────────────────────────────────

export default function App() {
  const [results, setResults] = useState<ApiResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAll = async () => {
    setLoading(true);
    setError(null);
    setResults([]);
    const acc: ApiResult[] = [];

    try {
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
      acc.push({ label: "QR Generation", data: qr.data });

      const nfc = await client.post("/api/v1/nfc", {
        issuer: "veilpass",
        payload: "https://veilpass.app/contact",
        version: "1.0",
        type: "uri",
        expiration: null,
        metadata: { department: "engineering" },
      });
      acc.push({ label: "NFC Payload", data: nfc.data });

      const link = await client.post("/api/v1/signed-link", {
        resource: "documents/nda-q3-2026.pdf",
        ttl: 86400,
        one_time: true,
        max_uses: 5,
      });
      acc.push({ label: "Signed Link", data: link.data });

      const signedUrl = await client.post("/api/v1/signed-url", {
        url: "https://storage.veilpass.app/reports/audit.pdf",
        permissions: "read",
        expires_in: 3600,
        download_limit: 10,
        one_time: false,
      });
      acc.push({ label: "Signed URL", data: signedUrl.data });

      const token = await client.post("/api/v1/token", {
        subject: "user_abc123",
        audience: "api.veilpass.app",
        issuer: "veilpass",
        expires_in: 86400,
        claims: { role: "admin", region: "us-east" },
      });
      acc.push({ label: "Token", data: token.data });

      const verify = await client.post("/api/v1/verify", {
        type: "token",
        value: token.data.token,
      });
      acc.push({ label: "Verification", data: verify.data });

      setResults(acc);
    } catch (e: any) {
      setError(e.response?.data ? JSON.stringify(e.response.data) : e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>VeilPass API Demo</Text>

      <TouchableOpacity style={styles.button} onPress={runAll} disabled={loading}>
        <Text style={styles.buttonText}>
          {loading ? "Running..." : "Run All API Operations"}
        </Text>
      </TouchableOpacity>

      {error && <Text style={styles.error}>Error: {error}</Text>}

      {results.map((r, i) => (
        <View key={i} style={styles.resultCard}>
          <Text style={styles.label}>{r.label}</Text>
          <Text style={styles.json}>
            {JSON.stringify(r.data, null, 2)}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#f5f5f5" },
  title: { fontSize: 24, fontWeight: "bold", marginBottom: 16, textAlign: "center" },
  button: {
    backgroundColor: "#4A90D9",
    padding: 14,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 16,
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  error: { color: "red", marginBottom: 12 },
  resultCard: {
    backgroundColor: "#fff",
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    elevation: 2,
  },
  label: { fontSize: 16, fontWeight: "bold", marginBottom: 4 },
  json: { fontSize: 12, fontFamily: "monospace" },
});
