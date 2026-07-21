const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(
      err.error?.message || `Request failed: ${res.status}`,
      res.status
    );
  }
  return res.json();
}

export const api = {
  qr: (data: Record<string, unknown>) =>
    request<{ data: string; format: string }>("/qr", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  nfc: (data: Record<string, unknown>) =>
    request<{ payload: Record<string, unknown>; hex: string; base64: string; ndef: string }>("/nfc", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  createSignedLink: (data: Record<string, unknown>) =>
    request<{ url: string; token: string; expiresAt: string }>("/signed-link", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  createSignedUrl: (data: Record<string, unknown>) =>
    request<{ url: string; components: Record<string, string> }>("/signed-url", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  createToken: (data: Record<string, unknown>) =>
    request<{ token: string; decoded: { header: Record<string, unknown>; payload: Record<string, unknown>; signature: string } }>("/token", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  verify: (data: Record<string, unknown>) =>
    request<{
      valid: boolean;
      expired: boolean;
      issuer?: string;
      claims?: Record<string, unknown>;
      signatureValid: boolean;
    }>("/verify", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export { ApiError };
