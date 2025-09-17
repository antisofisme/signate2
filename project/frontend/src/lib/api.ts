import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import Cookies from 'js-cookie';
import { ApiResponse, ApiError } from '@/types';

// API Client Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors and token refresh
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await this.refreshAuth(refreshToken);
              this.setTokens(response.data.accessToken, response.data.refreshToken);

              // Retry original request with new token
              originalRequest.headers.Authorization = `Bearer ${response.data.accessToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.clearTokens();
            window.location.href = '/auth/login';
            return Promise.reject(refreshError);
          }
        }

        // Transform axios error to our ApiError format
        const apiError: ApiError = {
          message: error.response?.data?.message || error.message || 'An unexpected error occurred',
          statusCode: error.response?.status || 500,
          error: error.response?.data?.error,
          details: error.response?.data?.details,
        };

        return Promise.reject(apiError);
      }
    );
  }

  // Token management
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return Cookies.get('auth_token') || null;
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return Cookies.get('refresh_token') || null;
  }

  public setTokens(accessToken: string, refreshToken: string): void {
    Cookies.set('auth_token', accessToken, {
      expires: 1, // 1 day
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });
    Cookies.set('refresh_token', refreshToken, {
      expires: 7, // 7 days
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });
  }

  public clearTokens(): void {
    Cookies.remove('auth_token');
    Cookies.remove('refresh_token');
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.client.post<ApiResponse<{
      user: any;
      tenant: any;
      accessToken: string;
      refreshToken: string;
    }>>('/api/v3/auth/login', { email, password });
    return response.data;
  }

  async register(userData: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    tenantName?: string;
  }) {
    const response = await this.client.post<ApiResponse<{
      user: any;
      tenant: any;
      accessToken: string;
      refreshToken: string;
    }>>('/api/v3/auth/register', userData);
    return response.data;
  }

  async logout() {
    const response = await this.client.post<ApiResponse<null>>('/api/v3/auth/logout');
    this.clearTokens();
    return response.data;
  }

  async refreshAuth(refreshToken: string) {
    const response = await this.client.post<ApiResponse<{
      accessToken: string;
      refreshToken: string;
    }>>('/api/v3/auth/refresh', { refreshToken });
    return response.data;
  }

  async getProfile() {
    const response = await this.client.get<ApiResponse<{ user: any; tenant: any }>>('/api/v3/auth/profile');
    return response.data;
  }

  async requestPasswordReset(email: string) {
    const response = await this.client.post<ApiResponse<null>>('/api/v3/auth/reset-password', { email });
    return response.data;
  }

  async resetPassword(token: string, newPassword: string) {
    const response = await this.client.post<ApiResponse<null>>('/api/v3/auth/reset-password/confirm', {
      token,
      newPassword,
    });
    return response.data;
  }

  async updatePassword(currentPassword: string, newPassword: string) {
    const response = await this.client.put<ApiResponse<null>>('/api/v3/auth/password', {
      currentPassword,
      newPassword,
    });
    return response.data;
  }

  // Content endpoints
  async getContent(params?: {
    page?: number;
    limit?: number;
    status?: string;
    type?: string;
    search?: string;
  }) {
    const response = await this.client.get<ApiResponse<any[]>>('/api/v3/content', { params });
    return response.data;
  }

  async getContentById(id: string) {
    const response = await this.client.get<ApiResponse<any>>(`/api/v3/content/${id}`);
    return response.data;
  }

  async createContent(contentData: any) {
    const response = await this.client.post<ApiResponse<any>>('/api/v3/content', contentData);
    return response.data;
  }

  async updateContent(id: string, contentData: any) {
    const response = await this.client.put<ApiResponse<any>>(`/api/v3/content/${id}`, contentData);
    return response.data;
  }

  async deleteContent(id: string) {
    const response = await this.client.delete<ApiResponse<null>>(`/api/v3/content/${id}`);
    return response.data;
  }

  // Users endpoints
  async getUsers(params?: {
    page?: number;
    limit?: number;
    role?: string;
    search?: string;
  }) {
    const response = await this.client.get<ApiResponse<any[]>>('/api/v3/users', { params });
    return response.data;
  }

  async getUserById(id: string) {
    const response = await this.client.get<ApiResponse<any>>(`/api/v3/users/${id}`);
    return response.data;
  }

  async updateUser(id: string, userData: any) {
    const response = await this.client.put<ApiResponse<any>>(`/api/v3/users/${id}`, userData);
    return response.data;
  }

  async deleteUser(id: string) {
    const response = await this.client.delete<ApiResponse<null>>(`/api/v3/users/${id}`);
    return response.data;
  }

  // Tenant endpoints
  async getTenantSettings() {
    const response = await this.client.get<ApiResponse<any>>('/api/v3/tenant/settings');
    return response.data;
  }

  async updateTenantSettings(settings: any) {
    const response = await this.client.put<ApiResponse<any>>('/api/v3/tenant/settings', settings);
    return response.data;
  }

  // Dashboard endpoints
  async getDashboardStats() {
    const response = await this.client.get<ApiResponse<any>>('/api/v3/dashboard/stats');
    return response.data;
  }

  // Generic request methods
  async get<T>(url: string, params?: any): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;