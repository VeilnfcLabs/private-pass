/// VeilPass API — Dart/Flutter example
///
/// Demonstrates all 6 API operations using the `http` package.
/// Run: dart run lib/main.dart
///
/// In a Flutter app, import this file and call the functions from your UI.

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

// ── Configuration ──────────────────────────────────────────────────────────────

const String _defaultBase = "http://localhost:8000";

String get _apiBase => Platform.environment['VEILPASS_API_URL'] ?? _defaultBase;
String get _apiKey => Platform.environment['VEILPASS_API_KEY'] ?? "";

Map<String, String> get _headers {
  var h = <String, String>{'Content-Type': 'application/json'};
  if (_apiKey.isNotEmpty) h['X-API-Key'] = _apiKey;
  return h;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

void log(String label, dynamic data) {
  print('\n── $label ──');
  print(data);
}

Future<Map<String, dynamic>> postJSON(String path, Map<String, dynamic> body) async {
  var uri = Uri.parse('$_apiBase$path');
  var response = await http.post(
    uri,
    headers: _headers,
    body: jsonEncode(body),
  );

  if (response.statusCode >= 400) {
    throw Exception("API error (HTTP ${response.statusCode}): ${response.body}");
  }

  return jsonDecode(response.body) as Map<String, dynamic>;
}

// ── 1. QR Generation ────────────────────────────────────────────────────────────

Future<Map<String, dynamic>> generateQR() async {
  var result = await postJSON("/api/v1/qr", {
    "content": "https://veilpass.app",
    "format": "png",
    "ecl": "H",
    "size": 512,
    "margin": 4,
    "color": "#000000",
    "bg_color": "#FFFFFF",
    "include_logo": false,
    "one_time": false,
    "expires_in": null,
  });
  log("QR Generation", result);
  return result;
}

// ── 2. NFC Payload ──────────────────────────────────────────────────────────────

Future<Map<String, dynamic>> generateNFC() async {
  var result = await postJSON("/api/v1/nfc", {
    "issuer": "veilpass",
    "payload": "https://veilpass.app/contact",
    "version": "1.0",
    "type": "uri",
    "expiration": null,
    "metadata": {"department": "engineering"},
  });
  log("NFC Payload", result);
  return result;
}

// ── 3. Signed Link ─────────────────────────────────────────────────────────────

Future<Map<String, dynamic>> createSignedLink() async {
  var result = await postJSON("/api/v1/signed-link", {
    "resource": "documents/nda-q3-2026.pdf",
    "ttl": 86400,
    "one_time": true,
    "max_uses": 5,
  });
  log("Signed Link", result);
  return result;
}

// ── 4. Signed URL ──────────────────────────────────────────────────────────────

Future<Map<String, dynamic>> createSignedURL() async {
  var result = await postJSON("/api/v1/signed-url", {
    "url": "https://storage.veilpass.app/reports/audit.pdf",
    "permissions": "read",
    "expires_in": 3600,
    "download_limit": 10,
    "one_time": false,
  });
  log("Signed URL", result);
  return result;
}

// ── 5. Token Generation ────────────────────────────────────────────────────────

Future<Map<String, dynamic>> generateToken() async {
  var result = await postJSON("/api/v1/token", {
    "subject": "user_abc123",
    "audience": "api.veilpass.app",
    "issuer": "veilpass",
    "expires_in": 86400,
    "claims": {"role": "admin", "region": "us-east"},
  });
  log("Token", result);
  return result;
}

// ── 6. Verification ─────────────────────────────────────────────────────────────

Future<Map<String, dynamic>> verify(String type, String value) async {
  var result = await postJSON("/api/v1/verify", {
    "type": type,
    "value": value,
  });
  log("Verification", result);
  return result;
}

// ── Main ────────────────────────────────────────────────────────────────────────

Future<void> main() async {
  try {
    await generateQR();
    await generateNFC();
    await createSignedLink();
    await createSignedURL();
    var token = await generateToken();
    await verify("token", token["token"] as String);

    print('\n✅ All API operations completed successfully.');
  } catch (e) {
    print('\n❌ Error: $e');
  }
}
