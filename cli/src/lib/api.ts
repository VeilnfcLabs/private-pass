import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface ApiConfig {
  baseURL: string;
  timeout: number;
  apiKey?: string;
}

export interface ApiError {
  status: number;
  message: string;
  code?: string;
  requestId?: string;
  details?: Record<string, unknown>;
}

class VeilPassAPI {
  private client: AxiosInstance;
  private config: ApiConfig;

  constructor(config?: Partial<ApiConfig>) {
    this.config = {
      baseURL: config?.baseURL || process.env.VEILPASS_API_URL || 'http://localhost:8000',
      timeout: config?.timeout || 10000,
      apiKey: config?.apiKey || process.env.VEILPASS_API_KEY,
    };

    this.client = axios.create({
      baseURL: `${this.config.baseURL}/api/v1`,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey ? { Authorization: `Bearer ${this.config.apiKey}` } : {}),
      },
    });

    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        const apiError: ApiError = {
          status: error.response?.status || 0,
          message: error.response?.data?.error?.message || error.response?.data?.message || error.message || 'Network error',
          code: error.response?.data?.error?.code,
          requestId: error.response?.data?.error?.request_id,
          details: error.response?.data?.details,
        };
        return Promise.reject(apiError);
      }
    );
  }

  setBaseURL(url: string): void {
    this.config.baseURL = url;
    this.client.defaults.baseURL = `${url}/api/v1`;
  }

  setApiKey(key: string): void {
    this.config.apiKey = key;
    this.client.defaults.headers.common['Authorization'] = `Bearer ${key}`;
  }

  async get<T = unknown>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(path, config);
    return response.data;
  }

  async post<T = unknown>(path: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(path, data, config);
    return response.data;
  }

  async health(): Promise<{ status: string; version: string; timestamp: string }> {
    return this.get('/health');
  }

  async createQR(data: { content: string; format?: string; ecl?: string; size?: number; margin?: number }) {
    return this.post<{ success: boolean; format: string; encoding: string; data: string; size: number; request_id: string }>('/qr', data);
  }

  async createNFC(data: { issuer?: string; payload: string; version?: string; type?: string }) {
    return this.post<{ success: boolean; id: string; type: string; version: string; issuer: string; timestamp: string; nonce: string; signature: string; payload: string; exports: Record<string, string>; request_id: string }>('/nfc', data);
  }

  async createSignedLink(data: { resource: string; ttl?: number; one_time?: boolean; max_uses?: number }) {
    return this.post<{ success: boolean; url: string; token: string; expires_at: string; signature: string; nonce: string; request_id: string }>('/signed-link', data);
  }

  async createSignedUrl(data: { url: string; permissions?: string; expires_in?: number; one_time?: boolean }) {
    return this.post<{ success: boolean; signed_url: string; expires: string; signature: string; key_id: string; request_id: string }>('/signed-url', data);
  }

  async createToken(data: { subject: string; audience?: string; issuer?: string; expires_in?: number; claims?: Record<string, unknown> }) {
    return this.post<{ success: boolean; token: string; decoded: { header: Record<string, unknown>; payload: Record<string, unknown> }; signature: string; expires_at: string; request_id: string }>('/token', data);
  }

  async verifyItem(data: { type: string; value: string }) {
    return this.post<{ success: boolean; valid: boolean; expired: boolean; issuer: string; signature_valid: boolean; claims: Record<string, unknown>; request_id: string }>('/verify', data);
  }
}

export { VeilPassAPI, ApiConfig };
export default VeilPassAPI;
