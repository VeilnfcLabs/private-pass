# VeilPass Flutter/Dart SDK Example

Demonstrates all 6 VeilPass API operations using the `http` package.

## Usage (Dart CLI)

```bash
# Default: http://localhost:8000
dart run lib/main.dart

# Custom API URL
VEILPASS_API_URL=https://api.veilpass.app dart run lib/main.dart

# With API key
VEILPASS_API_KEY=sk_xxx dart run lib/main.dart
```

## Usage (Flutter)

Import `lib/main.dart` functions into your Flutter app and call them from widgets.

## API Operations

| # | Endpoint | Description |
|---|----------|-------------|
| 1 | `POST /api/v1/qr` | Generate QR code (PNG/SVG) |
| 2 | `POST /api/v1/nfc` | Generate NFC payload |
| 3 | `POST /api/v1/signed-link` | Create signed link |
| 4 | `POST /api/v1/signed-url` | Create signed URL |
| 5 | `POST /api/v1/token` | Generate JWT token |
| 6 | `POST /api/v1/verify` | Verify token/link/URL |
