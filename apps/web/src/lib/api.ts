const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEFAULT_TIMEOUT = 15000;

export class ApiError extends Error {
  status: number;
  code: string;
  requestId: string;

  constructor(message: string, status: number, code = "UNKNOWN", requestId = "") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

export class NetworkError extends Error {
  constructor(cause: unknown) {
    super(cause instanceof Error ? cause.message : "Network request failed");
    this.name = "NetworkError";
    this.cause = cause;
  }
}

export class TimeoutError extends Error {
  constructor(ms: number) {
    super(`Request timed out after ${ms}ms`);
    this.name = "TimeoutError";
  }
}

async function request<T>(path: string, options?: RequestInit & { timeout?: number }): Promise<T> {
  const controller = new AbortController();
  const timeout = options?.timeout ?? DEFAULT_TIMEOUT;
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(`${API_BASE}/api/v1${path}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      signal: controller.signal,
      ...options,
    });

    if (!res.ok) {
      let errBody: Record<string, unknown> = {};
      try {
        errBody = await res.json();
      } catch {
        errBody = {};
      }
      const errorData = errBody.error as Record<string, unknown> | undefined;
      throw new ApiError(
        errorData?.message as string || `Request failed: ${res.status}`,
        res.status,
        errorData?.code as string || "UNKNOWN",
        (errorData?.request_id as string) || res.headers.get("X-Request-ID") || "",
      );
    }

    return res.json() as Promise<T>;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    if ((err as Error)?.name === "AbortError") throw new TimeoutError(timeout);
    if (err instanceof TypeError) throw new NetworkError(err);
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

interface QRResponse {
  success: boolean;
  format: string;
  encoding: string;
  data: string;
  content_type: string;
  size: number;
  expires_at: string | null;
  request_id: string;
}

interface NFCResponse {
  success: boolean;
  id: string;
  type: string;
  version: string;
  issuer: string;
  timestamp: string;
  nonce: string;
  signature: string;
  payload: string;
  exports: Record<string, string>;
  request_id: string;
}

interface SignedLinkResponse {
  success: boolean;
  url: string;
  token: string;
  expires_at: string;
  signature: string;
  nonce: string;
  request_id: string;
}

interface SignedURLResponse {
  success: boolean;
  signed_url: string;
  expires: string;
  signature: string;
  key_id: string;
  request_id: string;
}

interface TokenResponse {
  success: boolean;
  token: string;
  decoded: {
    header: Record<string, unknown>;
    payload: Record<string, unknown>;
  };
  signature: string;
  expires_at: string;
  request_id: string;
}

interface VerifyResponse {
  success: boolean;
  valid: boolean;
  expired: boolean;
  issuer: string;
  signature_valid: boolean;
  claims: Record<string, unknown>;
  request_id: string;
}

export const api = {
  async qr(data: Record<string, unknown>, timeout?: number): Promise<QRResponse> {
    return request<QRResponse>("/qr", {
      method: "POST",
      body: JSON.stringify(data),
      timeout,
    });
  },

  async nfc(data: Record<string, unknown>, timeout?: number): Promise<NFCResponse> {
    return request<NFCResponse>("/nfc", {
      method: "POST",
      body: JSON.stringify(data),
      timeout,
    });
  },

  async createSignedLink(data: Record<string, unknown>, timeout?: number): Promise<SignedLinkResponse> {
    return request<SignedLinkResponse>("/signed-link", {
      method: "POST",
      body: JSON.stringify(data),
      timeout,
    });
  },

  async createSignedUrl(data: Record<string, unknown>, timeout?: number): Promise<SignedURLResponse> {
    return request<SignedURLResponse>("/signed-url", {
      method: "POST",
      body: JSON.stringify(data),
      timeout,
    });
  },

  async createToken(data: Record<string, unknown>, timeout?: number): Promise<TokenResponse> {
    return request<TokenResponse>("/token", {
      method: "POST",
      body: JSON.stringify(data),
      timeout,
    });
  },

  async verify(data: Record<string, unknown>, timeout?: number): Promise<VerifyResponse> {
    return request<VerifyResponse>("/verify", {
      method: "POST",
      body: JSON.stringify(data),
      timeout,
    });
  },

  // SD-JWT
  async sdJwtGenerate(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/token/sd-jwt", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async sdJwtPresent(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/token/sd-jwt/present", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async sdJwtVerify(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/verify/sd-jwt", { method: "POST", body: JSON.stringify(data), timeout });
  },

  // ZKP
  async zkpKeypair(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/zkp/keypair", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async zkpProof(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/zkp/proof", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async zkpVerify(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/zkp/verify", { method: "POST", body: JSON.stringify(data), timeout });
  },

  // Ephemeral
  async ephemeralCreate(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/ephemeral", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async ephemeralVerify(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/ephemeral/verify", { method: "POST", body: JSON.stringify(data), timeout });
  },

  // Trust Registry
  async registryRegister(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/registry", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async registryList(): Promise<Record<string, unknown>> {
    return request("/registry");
  },
  async registryLookup(did: string): Promise<Record<string, unknown>> {
    return request(`/registry/${did}`);
  },
  async registryVerify(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/registry/verify", { method: "POST", body: JSON.stringify(data), timeout });
  },

  // Encrypted
  async encrypt(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/encrypted", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async decrypt(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/encrypted/decrypt", { method: "POST", body: JSON.stringify(data), timeout });
  },

  // Revocation
  async revoke(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/revoke", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async revokeStatus(id: string): Promise<Record<string, unknown>> {
    return request(`/revoke/status/${id}`);
  },

  // Dynamic QR
  async dynamicQrCreate(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/dynamic-qr", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async dynamicQrAnalytics(id: string): Promise<Record<string, unknown>> {
    return request(`/dynamic-qr/${id}/analytics`);
  },

  // Webhooks
  async webhookRegister(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/webhooks", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async webhookList(): Promise<Record<string, unknown>> {
    return request("/webhooks");
  },
  async webhookDelete(id: string): Promise<Record<string, unknown>> {
    return request(`/webhooks/${id}`, { method: "DELETE" });
  },

  // Keys
  async keyRotate(data: Record<string, unknown>, timeout?: number): Promise<Record<string, unknown>> {
    return request("/keys/rotate", { method: "POST", body: JSON.stringify(data), timeout });
  },
  async keyList(): Promise<Record<string, unknown>> {
    return request("/keys");
  },

  // Audit
  async auditLog(): Promise<Record<string, unknown>> {
    return request("/audit");
  },
  async auditExport(): Promise<Record<string, unknown>> {
    return request("/audit/export");
  },
};
