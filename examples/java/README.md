# VeilPass Java SDK Example

Demonstrates all 6 VeilPass API operations using `java.net.http.HttpClient` (Java 11+).

## Prerequisites

- Java 17+
- Maven 3.6+

## Usage

```bash
# Default: http://localhost:8000
mvn compile exec:java

# Custom API URL
VEILPASS_API_URL=https://api.veilpass.app mvn compile exec:java

# With API key
VEILPASS_API_KEY=sk_xxx mvn compile exec:java
```

## API Operations

| # | Endpoint | Description |
|---|----------|-------------|
| 1 | `POST /api/v1/qr` | Generate QR code (PNG/SVG) |
| 2 | `POST /api/v1/nfc` | Generate NFC payload |
| 3 | `POST /api/v1/signed-link` | Create signed link |
| 4 | `POST /api/v1/signed-url` | Create signed URL |
| 5 | `POST /api/v1/token` | Generate JWT token |
| 6 | `POST /api/v1/verify` | Verify token/link/URL |
