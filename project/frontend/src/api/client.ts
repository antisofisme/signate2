import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig
} from 'axios';
import { toast } from 'react-hot-toast';
import {
  ApiResponse,
  ErrorResponse,
  ApiClientConfig,
  ApiError,
  ApiErrorCode,
  RefreshTokenRequest,
  RefreshTokenResponse
} from '../types/api';
import { getStorageItem, setStorageItem, removeStorageItem } from '../utils/storage';
import { isOnline } from '../utils/network';
import { addToOfflineQueue } from '../utils/offline-queue';

export class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;
  private config: Required<ApiClientConfig>;

  constructor(config: ApiClientConfig) {
    this.config = {
      timeout: 10000,
      retryAttempts: 3,
      retryDelay: 1000,
      enableOfflineSupport: true,
      enableWebSockets: false,
      websocketURL: '',
      ...config
    };

    this.client = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      this.handleRequest.bind(this),
      this.handleRequestError.bind(this)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      this.handleResponse.bind(this),
      this.handleResponseError.bind(this)
    );
  }

  private async handleRequest(config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> {
    // Add authentication token
    const accessToken = getStorageItem('access_token');
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    // Add tenant context if available
    const tenantSlug = getStorageItem('current_tenant_slug');
    if (tenantSlug) {
      config.headers['X-Tenant-Slug'] = tenantSlug;
    }

    // Add request ID for tracking
    config.headers['X-Request-ID'] = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Check network status for offline support
    if (this.config.enableOfflineSupport && !isOnline()) {
      // Queue request for later if offline
      await addToOfflineQueue({
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        method: config.method?.toUpperCase() || 'GET',
        url: config.url || '',
        data: config.data,
        headers: config.headers as Record<string, string>,
        timestamp: new Date().toISOString(),
        retryCount: 0,
        maxRetries: this.config.retryAttempts,
      });

      throw new ApiError(
        ApiErrorCode.NETWORK_ERROR,
        'No internet connection. Request queued for later.',
        0
      );
    }

    return config;
  }

  private handleRequestError(error: any): Promise<never> {
    return Promise.reject(this.createApiError(error));
  }

  private handleResponse(response: AxiosResponse): AxiosResponse {
    // Log rate limit headers if present
    const rateLimitRemaining = response.headers['x-ratelimit-remaining'];
    const rateLimitReset = response.headers['x-ratelimit-reset'];

    if (rateLimitRemaining && parseInt(rateLimitRemaining) < 10) {
      console.warn(`Rate limit warning: ${rateLimitRemaining} requests remaining`);

      if (parseInt(rateLimitRemaining) < 5) {
        toast.error('Rate limit approaching. Please slow down your requests.');
      }
    }

    return response;
  }

  private async handleResponseError(error: any): Promise<never> {
    const originalRequest = error.config;

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const newAccessToken = await this.refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return this.client(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        this.handleAuthenticationFailure();
        throw this.createApiError(refreshError);
      }
    }

    // Handle other HTTP errors
    throw this.createApiError(error);
  }

  private async refreshAccessToken(): Promise<string> {
    // Prevent multiple simultaneous refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._performTokenRefresh();

    try {
      const token = await this.refreshPromise;
      this.refreshPromise = null;
      return token;
    } catch (error) {
      this.refreshPromise = null;
      throw error;
    }
  }

  private async _performTokenRefresh(): Promise<string> {
    const refreshToken = getStorageItem('refresh_token');
    if (!refreshToken) {
      throw new ApiError(ApiErrorCode.UNAUTHORIZED, 'No refresh token available');
    }

    try {
      const response = await axios.post<ApiResponse<RefreshTokenResponse>>(
        `${this.config.baseURL}/api/auth/refresh/`,
        {
          refresh_token: refreshToken,
          device_info: {
            user_agent: navigator.userAgent,
            platform: navigator.platform,
          }
        } as RefreshTokenRequest,
        {
          timeout: this.config.timeout,
        }
      );

      if (response.data.success && response.data.data) {
        const { access_token, refresh_token: newRefreshToken } = response.data.data;

        setStorageItem('access_token', access_token);
        setStorageItem('refresh_token', newRefreshToken);

        return access_token;
      } else {
        throw new ApiError(ApiErrorCode.UNAUTHORIZED, 'Token refresh failed');
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw new ApiError(ApiErrorCode.UNAUTHORIZED, 'Failed to refresh authentication token');
    }
  }

  private handleAuthenticationFailure(): void {
    // Clear stored tokens
    removeStorageItem('access_token');
    removeStorageItem('refresh_token');
    removeStorageItem('current_user');
    removeStorageItem('current_tenant');

    // Show user notification
    toast.error('Your session has expired. Please log in again.');

    // Redirect to login (you might want to use your routing solution here)
    window.location.href = '/login';
  }

  private createApiError(error: any): ApiError {
    if (error.code === 'ECONNABORTED') {
      return new ApiError(
        ApiErrorCode.TIMEOUT_ERROR,
        'Request timeout',
        0,
        { timeout: this.config.timeout }
      );
    }

    if (!error.response) {
      return new ApiError(
        ApiErrorCode.NETWORK_ERROR,
        'Network error occurred',
        0,
        { originalError: error.message }
      );
    }

    const { status, data } = error.response;
    const errorResponse = data as ErrorResponse;

    // Map HTTP status to error codes
    let code: ApiErrorCode;
    switch (status) {
      case 400:
        code = ApiErrorCode.VALIDATION_ERROR;
        break;
      case 401:
        code = ApiErrorCode.UNAUTHORIZED;
        break;
      case 403:
        code = ApiErrorCode.PERMISSION_DENIED;
        break;
      case 404:
        code = ApiErrorCode.NOT_FOUND;
        break;
      case 429:
        code = errorResponse.error === 'QUOTA_EXCEEDED'
          ? ApiErrorCode.QUOTA_EXCEEDED
          : ApiErrorCode.RATE_LIMITED;
        break;
      default:
        code = ApiErrorCode.SERVER_ERROR;
    }

    return new ApiError(
      code,
      errorResponse.message || 'An error occurred',
      status,
      {
        details: errorResponse.details,
        request_id: errorResponse.request_id,
      }
    );
  }

  // Generic request method with retry logic
  private async request<T>(
    config: AxiosRequestConfig,
    retryCount: number = 0
  ): Promise<T> {
    try {
      const response = await this.client.request<ApiResponse<T>>(config);

      if (response.data.success) {
        return response.data.data as T;
      } else {
        throw new ApiError(
          ApiErrorCode.SERVER_ERROR,
          response.data.message || 'Request failed',
          response.status
        );
      }
    } catch (error) {
      // Retry logic for transient errors
      if (
        retryCount < this.config.retryAttempts &&
        this.shouldRetry(error as ApiError)
      ) {
        const delay = this.config.retryDelay * Math.pow(2, retryCount); // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.request<T>(config, retryCount + 1);
      }

      throw error;
    }
  }

  private shouldRetry(error: ApiError): boolean {
    // Retry on network errors, timeouts, and 5xx server errors
    return [
      ApiErrorCode.NETWORK_ERROR,
      ApiErrorCode.TIMEOUT_ERROR,
      ApiErrorCode.SERVER_ERROR,
    ].includes(error.code) || (error.status ? error.status >= 500 : false);
  }

  // Public API methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({
      method: 'GET',
      url,
      ...config,
    });
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url,
      data,
      ...config,
    });
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({
      method: 'PUT',
      url,
      data,
      ...config,
    });
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({
      method: 'PATCH',
      url,
      data,
      ...config,
    });
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({
      method: 'DELETE',
      url,
      ...config,
    });
  }

  // File upload with progress tracking
  async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (progress: { loaded: number; total: number; percentage: number }) => void,
    additionalData?: Record<string, any>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
      });
    }

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = {
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage: Math.round((progressEvent.loaded * 100) / progressEvent.total),
          };
          onProgress(progress);
        }
      },
    });
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health/');
      return true;
    } catch {
      return false;
    }
  }

  // Update base configuration
  updateConfig(config: Partial<ApiClientConfig>): void {
    this.config = { ...this.config, ...config };

    if (config.baseURL) {
      this.client.defaults.baseURL = config.baseURL;
    }

    if (config.timeout) {
      this.client.defaults.timeout = config.timeout;
    }
  }

  // Get current configuration
  getConfig(): Readonly<Required<ApiClientConfig>> {
    return { ...this.config };
  }
}

// Create default API client instance
export const apiClient = new ApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v3',
  enableOfflineSupport: true,
  enableWebSockets: true,
  websocketURL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
});

// Export configured instance
export default apiClient;