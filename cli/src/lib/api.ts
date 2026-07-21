import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface ApiConfig {
  baseURL: string;
  timeout: number;
  apiKey?: string;
}

interface ApiError {
  status: number;
  message: string;
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
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey ? { 'X-API-Key': this.config.apiKey } : {}),
      },
    });

    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response) {
          const apiError: ApiError = {
            status: error.response.status,
            message: error.response.data?.message || error.message,
            details: error.response.data?.details,
          };
          return Promise.reject(apiError);
        }
        return Promise.reject({
          status: 0,
          message: error.message || 'Network error',
        });
      }
    );
  }

  setBaseURL(url: string): void {
    this.config.baseURL = url;
    this.client.defaults.baseURL = url;
  }

  setApiKey(key: string): void {
    this.config.apiKey = key;
    this.client.defaults.headers['X-API-Key'] = key;
  }

  async get<T = unknown>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(path, config);
    return response.data;
  }

  async post<T = unknown>(path: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(path, data, config);
    return response.data;
  }

  async put<T = unknown>(path: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(path, data, config);
    return response.data;
  }

  async delete<T = unknown>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(path, config);
    return response.data;
  }

  async health(): Promise<{ status: string; version: string }> {
    return this.get('/api/health');
  }

  async createQR(data: { content: string; options?: Record<string, unknown> }) {
    return this.post<{ qr_code: string; id: string }>('/api/qr', data);
  }

  async createToken(data: { sub: string; ttl?: number; claims?: Record<string, unknown> }) {
    return this.post<{ token: string; expires_at: string }>('/api/tokens', data);
  }

  async verifyToken(token: string) {
    return this.post<{ valid: boolean; payload: Record<string, unknown> }>('/api/verify/token', { token });
  }

  async createLink(data: { resource: string; ttl?: number; one_time?: boolean; max_uses?: number }) {
    return this.post<{ url: string; id: string; expires_at: string }>('/api/links', data);
  }
}

export { VeilPassAPI, ApiConfig, ApiError };
export default VeilPassAPI;
