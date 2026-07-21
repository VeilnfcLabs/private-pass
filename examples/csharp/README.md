# VeilPass C# SDK Example

Demonstrates all 6 VeilPass API operations using `System.Net.Http.HttpClient`.

## Prerequisites

- .NET 8.0 SDK

## Usage

```bash
# Default: http://localhost:8000
dotnet run

# Custom API URL
$env:VEILPASS_API_URL="https://api.veilpass.app"; dotnet run

# With API key
$env:VEILPASS_API_KEY="sk_xxx"; dotnet run
```

## Files

| File | Description |
|------|-------------|
| `Program.cs` | Entry point — calls all 6 operations |
| `VeilPassClient.cs` | Reusable API client wrapper class |

## API Operations

| # | Endpoint | Description |
|---|----------|-------------|
| 1 | `POST /api/v1/qr` | Generate QR code (PNG/SVG) |
| 2 | `POST /api/v1/nfc` | Generate NFC payload |
| 3 | `POST /api/v1/signed-link` | Create signed link |
| 4 | `POST /api/v1/signed-url` | Create signed URL |
| 5 | `POST /api/v1/token` | Generate JWT token |
| 6 | `POST /api/v1/verify` | Verify token/link/URL |
