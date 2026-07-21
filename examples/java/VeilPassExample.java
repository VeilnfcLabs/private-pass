/**
 * VeilPass API — Java example
 *
 * Demonstrates all 6 API operations using java.net.http.HttpClient (Java 11+).
 * Compile: javac VeilPassExample.java
 * Run:     java VeilPassExample
 */

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class VeilPassExample {

    // ── Configuration ──────────────────────────────────────────────────────────

    private static final String API_BASE = System.getenv().getOrDefault("VEILPASS_API_URL", "http://localhost:8000");
    private static final String API_KEY = System.getenv().getOrDefault("VEILPASS_API_KEY", "");

    private static final HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(15))
            .build();

    // ── Helpers ────────────────────────────────────────────────────────────────

    private static void log(String label, String json) {
        System.out.println("\n── " + label + " ──");
        try {
            var obj = new com.google.gson.GsonBuilder().setPrettyPrinting().create().toJson(
                com.google.gson.JsonParser.parseString(json)
            );
            System.out.println(obj);
        } catch (Exception e) {
            System.out.println(json);
        }
    }

    private static String postJSON(String path, String body) throws Exception {
        var url = java.net.URI.create(API_BASE + path).toURL();
        var conn = (java.net.HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        if (!API_KEY.isEmpty()) {
            conn.setRequestProperty("X-API-Key", API_KEY);
        }
        conn.setDoOutput(true);

        try (var os = conn.getOutputStream()) {
            os.write(body.getBytes());
        }

        var sb = new StringBuilder();
        try (var reader = new java.io.BufferedReader(
                new java.io.InputStreamReader(
                    conn.getResponseCode() < 400 ? conn.getInputStream() : conn.getErrorStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
        }

        if (conn.getResponseCode() >= 400) {
            throw new RuntimeException("API error (HTTP " + conn.getResponseCode() + "): " + sb);
        }

        return sb.toString();
    }

    private static void log(String label, String json) {
        System.out.println("\n── " + label + " ──");
        try {
            var gson = new com.google.gson.GsonBuilder().setPrettyPrinting().create();
            var element = com.google.gson.JsonParser.parseString(json);
            System.out.println(gson.toJson(element));
        } catch (Exception e) {
            System.out.println(json);
        }
    }

    // ── 1. QR Generation ──────────────────────────────────────────────────────

    private static String generateQR() throws Exception {
        String body = """
            {
                "content": "https://veilpass.app",
                "format": "png",
                "ecl": "H",
                "size": 512,
                "margin": 4,
                "color": "#000000",
                "bg_color": "#FFFFFF",
                "include_logo": false,
                "one_time": false,
                "expires_in": null
            }
            """;
        String json = postJSON("/api/v1/qr", body);
        log("QR Generation", json);
        return json;
    }

    // ── 2. NFC Payload ──────────────────────────────────────────────────────────

    private static String generateNFC() throws Exception {
        String body = """
            {
                "issuer": "veilpass",
                "payload": "https://veilpass.app/contact",
                "version": "1.0",
                "type": "uri",
                "expiration": null,
                "metadata": { "department": "engineering" }
            }
            """;
        String json = postJSON("/api/v1/nfc", body);
        log("NFC Payload", json);
        return json;
    }

    // ── 3. Signed Link ─────────────────────────────────────────────────────────

    private static String createSignedLink() throws Exception {
        String body = """
            {
                "resource": "documents/nda-q3-2026.pdf",
                "ttl": 86400,
                "one_time": true,
                "max_uses": 5
            }
            """;
        String json = postJSON("/api/v1/signed-link", body);
        log("Signed Link", json);
        return json;
    }

    // ── 4. Signed URL ──────────────────────────────────────────────────────────

    private static String createSignedURL() throws Exception {
        String body = """
            {
                "url": "https://storage.veilpass.app/reports/audit.pdf",
                "permissions": "read",
                "expires_in": 3600,
                "download_limit": 10,
                "one_time": false
            }
            """;
        String json = postJSON("/api/v1/signed-url", body);
        log("Signed URL", json);
        return json;
    }

    // ── 5. Token Generation ────────────────────────────────────────────────────

    private static String generateToken() throws Exception {
        String body = """
            {
                "subject": "user_abc123",
                "audience": "api.veilpass.app",
                "issuer": "veilpass",
                "expires_in": 86400,
                "claims": { "role": "admin", "region": "us-east" }
            }
            """;
        String json = postJSON("/api/v1/token", body);
        log("Token", json);
        return json;
    }

    // ── 6. Verification ─────────────────────────────────────────────────────────

    private static String verify(String type, String value) throws Exception {
        String body = """
            {
                "type": "%s",
                "value": "%s"
            }
            """.formatted(type, value);
        String json = postJSON("/api/v1/verify", body);
        log("Verification", json);
        return json;
    }

    // ── Main ────────────────────────────────────────────────────────────────────

    public static void main(String[] args) throws Exception {
        generateQR();
        generateNFC();
        createSignedLink();
        createSignedURL();
        String tokenJson = generateToken();

        var root = com.google.gson.JsonParser.parseString(tokenJson).getAsJsonObject();
        String token = root.get("token").getAsString();
        verify("token", token);

        System.out.println("\n✅ All API operations completed successfully.");
    }
}
