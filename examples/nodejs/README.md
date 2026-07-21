# VeilPass Node.js SDK Example

Demonstrates all 6 VeilPass API operations using axios.

## Setup

```bash
npm install
```

## Usage

```bash
# Default: http://localhost:8000
npm start

# Custom API URL
VEILPASS_API_URL=https://api.veilpass.app npm start

# With API key
VEILPASS_API_KEY=sk_xxx npm start
```

## Files

| File | Description |
|------|-------------|
| `index.js` | ESM example (import/export) |
| `index.cjs` | CommonJS example (require) |
| `package.json` | Dependencies and scripts |

## API Operations

| # | Endpoint | Description |
|---|----------|-------------|
| 1 | `POST /api/v1/qr` | Generate QR code (PNG/SVG) |
| 2 | `POST /api/v1/nfc` | Generate NFC payload |
| 3 | `POST /api/v1/signed-link` | Create signed link |
| 4 | `POST /api/v1/signed-url` | Create signed URL |
| 5 | `POST /api/v1/token` | Generate JWT token |
| 6 | `POST /api/v1/verify` | Verify token/link/URL |
