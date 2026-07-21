package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// ── Configuration ──────────────────────────────────────────────────────────────

var apiBase = getEnv("VEILPASS_API_URL", "http://localhost:8000")
var apiKey = getEnv("VEILPASS_API_KEY", "")

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// ── Helpers ────────────────────────────────────────────────────────────────────

func log(label string, data any) {
	b, _ := json.MarshalIndent(data, "", "  ")
	fmt.Printf("\n── %s ──\n%s\n", label, string(b))
}

func postJSON(url string, body any) (map[string]any, error) {
	b, _ := json.Marshal(body)
	req, _ := http.NewRequest("POST", url, bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	if apiKey != "" {
		req.Header.Set("X-API-Key", apiKey)
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer res.Body.Close()

	var result map[string]any
	if err := json.NewDecoder(res.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode failed: %w", err)
	}

	if res.StatusCode >= 400 {
		return result, fmt.Errorf("API error (HTTP %d)", res.StatusCode)
	}

	return result, nil
}

// ── 1. QR Generation ────────────────────────────────────────────────────────────

func generateQR() {
	result, err := postJSON(apiBase+"/api/v1/qr", map[string]any{
		"content":      "https://veilpass.app",
		"format":       "png",
		"ecl":          "H",
		"size":         512,
		"margin":       4,
		"color":        "#000000",
		"bg_color":     "#FFFFFF",
		"include_logo": false,
		"one_time":     false,
		"expires_in":   nil,
	})
	if err != nil {
		logFatal("QR generation", err)
	}
	log("QR Generation", result)
}

// ── 2. NFC Payload ──────────────────────────────────────────────────────────────

func generateNFC() {
	result, err := postJSON(apiBase+"/api/v1/nfc", map[string]any{
		"issuer":     "veilpass",
		"payload":    "https://veilpass.app/contact",
		"version":    "1.0",
		"type":       "uri",
		"expiration": nil,
		"metadata":   map[string]any{"department": "engineering"},
	})
	if err != nil {
		logFatal("NFC generation", err)
	}
	log("NFC Payload", result)
}

// ── 3. Signed Link ─────────────────────────────────────────────────────────────

func createSignedLink() {
	result, err := postJSON(apiBase+"/api/v1/signed-link", map[string]any{
		"resource": "documents/nda-q3-2026.pdf",
		"ttl":      86400,
		"one_time": true,
		"max_uses": 5,
	})
	if err != nil {
		logFatal("Signed link creation", err)
	}
	log("Signed Link", result)
}

// ── 4. Signed URL ──────────────────────────────────────────────────────────────

func createSignedURL() {
	result, err := postJSON(apiBase+"/api/v1/signed-url", map[string]any{
		"url":            "https://storage.veilpass.app/reports/audit.pdf",
		"permissions":    "read",
		"expires_in":     3600,
		"download_limit": 10,
		"one_time":       false,
	})
	if err != nil {
		logFatal("Signed URL creation", err)
	}
	log("Signed URL", result)
}

// ── 5. Token Generation ────────────────────────────────────────────────────────

func generateToken() {
	result, err := postJSON(apiBase+"/api/v1/token", map[string]any{
		"subject":    "user_abc123",
		"audience":   "api.veilpass.app",
		"issuer":     "veilpass",
		"expires_in": 86400,
		"claims":     map[string]any{"role": "admin", "region": "us-east"},
	})
	if err != nil {
		logFatal("Token generation", err)
	}
	log("Token", result)
}

// ── 6. Verification ─────────────────────────────────────────────────────────────

func verifyToken(token string) {
	result, err := postJSON(apiBase+"/api/v1/verify", map[string]any{
		"type":  "token",
		"value": token,
	})
	if err != nil {
		logFatal("Verification", err)
	}
	log("Verification", result)
}

// ── Main ────────────────────────────────────────────────────────────────────────

func main() {
	generateQR()
	generateNFC()
	createSignedLink()
	createSignedURL()
	generateToken()
	verifyToken(token)

	fmt.Println("\n✅ All API operations completed successfully.")
}
